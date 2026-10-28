"""Alertas de prazo: avisa quem recebeu uma recomendação quando a inscrição está para fechar."""
import logging

from .. import config
from ..db import buscar_todos, executar
from . import push

log = logging.getLogger(__name__)

JANELAS = (("prazo_7d", 7), ("prazo_1d", 1))


async def enviar_alertas_de_prazo() -> int:
    total = 0
    for tipo, dias in JANELAS:
        pendentes = await buscar_todos(
            """select distinct r.usuario_id, i.id as investidor_id, i.nome, i.inscricao_fecha
                 from recomendacoes r join investidores i on i.id = r.investidor_id
                where i.inscricao_fecha = current_date + %(dias)s
                  and (r.salvo or r.aderencia >= 60)
                  and not exists (select 1 from alertas_enviados a
                                   where a.usuario_id = r.usuario_id and a.investidor_id = i.id and a.tipo = %(tipo)s)""",
            {"dias": dias, "tipo": tipo},
        )
        for p in pendentes:
            quando = "amanhã" if dias == 1 else f"em {dias} dias"
            await push.enviar(p["usuario_id"], f"Inscrição fecha {quando}",
                              f"{p['nome']}: não perca o prazo ({p['inscricao_fecha']:%d/%m}).",
                              f"{config.SITE_URL}/app/oportunidades")
            await executar("insert into alertas_enviados (usuario_id, investidor_id, tipo) values (%s, %s, %s) "
                           "on conflict do nothing", (p["usuario_id"], p["investidor_id"], tipo))
            total += 1
    log.info("Alertas de prazo enviados: %s", total)
    return total
