"""Cadastro de notificações push (PWA e apps nativos)."""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .. import config
from ..auth import Usuario, usuario_atual
from ..db import Jsonb, executar

rota = APIRouter(prefix="/api/push")


@rota.get("/chave-publica")
async def chave_publica():
    return {"chave": config.VAPID_PUBLIC_KEY}


class Inscricao(BaseModel):
    plataforma: Literal["web", "android", "ios"]
    endpoint: str          # web push: subscription.endpoint | nativo: token FCM
    chaves: dict | None = None  # web push: {"p256dh": ..., "auth": ...}


@rota.post("/inscrever")
async def inscrever(insc: Inscricao, usuario: Usuario = Depends(usuario_atual)):
    await executar(
        """insert into push_inscricoes (usuario_id, plataforma, endpoint, chaves) values (%s, %s, %s, %s)
           on conflict (endpoint) do update set usuario_id = excluded.usuario_id, chaves = excluded.chaves""",
        (usuario.id, insc.plataforma, insc.endpoint, Jsonb(insc.chaves) if insc.chaves else None),
    )
    return {"ok": True}


class Cancelamento(BaseModel):
    endpoint: str


@rota.post("/cancelar")
async def cancelar(c: Cancelamento, usuario: Usuario = Depends(usuario_atual)):
    await executar("delete from push_inscricoes where endpoint = %s and usuario_id = %s", (c.endpoint, usuario.id))
    return {"ok": True}
