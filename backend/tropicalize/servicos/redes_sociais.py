"""Envio dos posts aprovados para as redes sociais.

Cada post vai para um webhook (Make, Zapier, n8n ou o agendador que você usar), que
publica no Instagram, LinkedIn, X e Threads. A imagem do card é gerada pelo site em
/blog/<slug>/opengraph-image.
"""
import logging

import httpx

from .. import config
from ..db import buscar_todos, executar

log = logging.getLogger(__name__)


async def enviar_posts_da_noticia(noticia_id: int) -> int:
    if not config.WEBHOOK_REDES_SOCIAIS:
        return 0
    posts = await buscar_todos(
        """select p.id, p.rede, p.texto, n.slug, n.titulo
             from posts_sociais p join noticias n on n.id = p.noticia_id
            where p.noticia_id = %s and p.status <> 'enviado'""",
        (noticia_id,),
    )
    enviados = 0
    async with httpx.AsyncClient(timeout=20) as http:
        for p in posts:
            link = f"{config.SITE_URL}/blog/{p['slug']}"
            try:
                r = await http.post(config.WEBHOOK_REDES_SOCIAIS, json={
                    "rede": p["rede"], "texto": p["texto"], "titulo": p["titulo"], "link": link,
                    "imagem": f"{link}/opengraph-image",
                })
                r.raise_for_status()
                await executar("update posts_sociais set status = 'enviado', enviado_em = now() where id = %s", (p["id"],))
                enviados += 1
            except httpx.HTTPError:
                log.exception("Falha ao enviar post %s", p["id"])
                await executar("update posts_sociais set status = 'erro' where id = %s", (p["id"],))
    return enviados
