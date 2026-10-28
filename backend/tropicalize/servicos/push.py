"""Envio de notificações: web push (PWA) e FCM (apps Android/iOS via Capacitor)."""
import asyncio
import json
import logging

from .. import config
from ..db import buscar_todos, executar

log = logging.getLogger(__name__)
_firebase = None


def _app_firebase():
    global _firebase
    if _firebase is None and config.FIREBASE_CREDENCIAIS_JSON:
        import firebase_admin
        from firebase_admin import credentials
        _firebase = firebase_admin.initialize_app(
            credentials.Certificate(json.loads(config.FIREBASE_CREDENCIAIS_JSON)))
    return _firebase


def _web_push(insc: dict, payload: dict) -> bool:
    from pywebpush import WebPushException, webpush
    try:
        webpush(
            subscription_info={"endpoint": insc["endpoint"], "keys": insc["chaves"]},
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=config.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": config.VAPID_CONTATO},
        )
        return True
    except WebPushException as e:
        if e.response is not None and e.response.status_code in (404, 410):
            return False  # inscrição expirada
        log.warning("Web push falhou: %s", e)
        return True


def _fcm(insc: dict, payload: dict) -> bool:
    from firebase_admin import messaging
    try:
        messaging.send(messaging.Message(
            token=insc["endpoint"],
            notification=messaging.Notification(title=payload["titulo"], body=payload["corpo"]),
            data={"url": payload["url"]},
        ), app=_app_firebase())
        return True
    except messaging.UnregisteredError:
        return False
    except Exception:  # noqa: BLE001
        log.exception("FCM falhou")
        return True


async def enviar(usuario_id: str, titulo: str, corpo: str, url: str) -> int:
    inscricoes = await buscar_todos("select id, plataforma, endpoint, chaves from push_inscricoes where usuario_id = %s",
                                    (usuario_id,))
    payload = {"titulo": titulo, "corpo": corpo, "url": url}
    enviados = 0
    for insc in inscricoes:
        if insc["plataforma"] == "web":
            if not config.VAPID_PRIVATE_KEY:
                continue
            valido = await asyncio.to_thread(_web_push, insc, payload)
        else:
            if not _app_firebase():
                continue
            valido = await asyncio.to_thread(_fcm, insc, payload)
        if valido:
            enviados += 1
        else:
            await executar("delete from push_inscricoes where id = %s", (insc["id"],))
    return enviados
