"""Análises dos 4 modos (streaming via SSE), relatórios salvos e oportunidades."""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from .. import config, llm, modos
from ..auth import Usuario, consumir_cota, devolver_cota, usuario_atual
from ..db import Jsonb, buscar_todos, buscar_um, executar

log = logging.getLogger(__name__)
rota = APIRouter(prefix="/api")

# A geração continua mesmo se o app fechar ou perder conexão: o relatório fica salvo.
_tarefas: set[asyncio.Task] = set()
FIM = object()


@rota.get("/eu")
async def eu(usuario: Usuario = Depends(usuario_atual)):
    uso = await buscar_um(
        "select analises from uso_mensal where usuario_id = %s and mes = date_trunc('month', now())::date",
        (usuario.id,),
    )
    limite = config.COTA_MENSAL.get(usuario.plano, 0)
    return {"id": usuario.id, "email": usuario.email, "plano": usuario.plano, "admin": usuario.admin,
            "analises_restantes": max(limite - (uso["analises"] if uso else 0), 0), "cota_mensal": limite}


@rota.post("/analises/{modo}")
async def criar_analise(modo: str, request: Request, usuario: Usuario = Depends(usuario_atual)):
    if modo not in modos.ENTRADAS:
        raise HTTPException(404, "Modo inexistente")
    try:
        entrada = modos.ENTRADAS[modo].model_validate(await request.json())
    except (ValidationError, json.JSONDecodeError) as e:
        raise HTTPException(422, f"Dados inválidos: {e}") from e

    relatorio_origem = None
    if getattr(entrada, "relatorio_origem_id", None):
        origem = await buscar_um("select conteudo from relatorios where id = %s and usuario_id = %s",
                                 (entrada.relatorio_origem_id, usuario.id))
        relatorio_origem = origem["conteudo"] if origem else None

    await consumir_cota(usuario)
    linha = await buscar_um(
        "insert into relatorios (usuario_id, modo, titulo, entrada, modelo) values (%s, %s, %s, %s, %s) returning id",
        (usuario.id, modo, modos.titulo(modo, entrada), Jsonb(entrada.model_dump()), config.MODELO_PROFUNDO),
    )
    relatorio_id = linha["id"]
    fila: asyncio.Queue = asyncio.Queue()
    tarefa = asyncio.create_task(_gerar(relatorio_id, modo, entrada, relatorio_origem, usuario, fila))
    _tarefas.add(tarefa)
    tarefa.add_done_callback(_tarefas.discard)

    async def eventos():
        yield _sse({"tipo": "inicio", "relatorio_id": relatorio_id})
        while True:
            try:
                ev = await asyncio.wait_for(fila.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ": mantendo conexão\n\n"  # evita que proxies derrubem a conexão ociosa
                continue
            if ev is FIM:
                return
            yield _sse(ev)

    return StreamingResponse(eventos(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _sse(dados: dict) -> str:
    return f"data: {json.dumps(dados, ensure_ascii=False, default=str)}\n\n"


async def _gerar(relatorio_id: int, modo: str, entrada, relatorio_origem, usuario: Usuario, fila: asyncio.Queue):
    texto: list[str] = []
    fontes: list[dict] = []
    try:
        fila.put_nowait({"tipo": "status", "texto": "Buscando referências na base do Tropicalize"})
        mensagem, extra = await modos.montar_mensagem(modo, entrada, relatorio_origem)
        final = None
        async for ev in llm.gerar_relatorio(modos.sistema(modo, entrada), mensagem):
            if ev["tipo"] == "texto":
                texto.append(ev["texto"])
            elif ev["tipo"] == "fonte":
                fontes.append({"titulo": ev["titulo"], "url": ev["url"]})
            if ev["tipo"] in ("fim", "erro"):
                final = ev
            else:
                fila.put_nowait(ev)

        conteudo = "".join(texto)
        if final is None or final["tipo"] == "erro":
            await executar("update relatorios set status = 'erro', conteudo = %s, fontes = %s where id = %s",
                           (conteudo, Jsonb(fontes), relatorio_id))
            if not conteudo:
                await devolver_cota(usuario)
            fila.put_nowait(final or {"tipo": "erro", "texto": "A análise não terminou."})
            return

        estruturado = None
        if modo == "captar":
            fila.put_nowait({"tipo": "status", "texto": "Organizando as recomendações"})
            estruturado = await _salvar_recomendacoes(relatorio_id, usuario.id, conteudo, extra["candidatos"])
            fila.put_nowait({"tipo": "recomendacoes", "itens": estruturado})

        await executar(
            """update relatorios set status = 'pronto', conteudo = %s, fontes = %s, estruturado = %s,
                      modelo = %s, tokens_entrada = %s, tokens_saida = %s where id = %s""",
            (conteudo, Jsonb(fontes), Jsonb(estruturado) if estruturado is not None else None,
             final["modelo"], final["tokens_entrada"], final["tokens_saida"], relatorio_id),
        )
        fila.put_nowait({"tipo": "fim", "relatorio_id": relatorio_id})
    except Exception:
        log.exception("Falha ao gerar relatório %s", relatorio_id)
        await executar("update relatorios set status = 'erro', conteudo = %s where id = %s",
                       ("".join(texto), relatorio_id))
        if not texto:
            await devolver_cota(usuario)
        fila.put_nowait({"tipo": "erro", "texto": "Erro interno ao gerar a análise."})
    finally:
        fila.put_nowait(FIM)


async def _salvar_recomendacoes(relatorio_id: int, usuario_id: str, conteudo: str, candidatos: dict) -> list[dict]:
    res = await llm.estruturar(modos.INSTRUCAO_EXTRAIR, conteudo, modos.Recomendacoes)
    itens = []
    for r in (res.recomendacoes if res else []):
        c = candidatos.get(r.investidor_id)
        if c is None:  # o modelo citou um id fora da lista de candidatos: descarta
            continue
        aderencia = max(0, min(100, r.aderencia))
        await executar(
            """insert into recomendacoes (relatorio_id, investidor_id, usuario_id, aderencia, motivo)
               values (%s, %s, %s, %s, %s) on conflict do nothing""",
            (relatorio_id, c["id"], usuario_id, aderencia, r.motivo),
        )
        itens.append({"investidor_id": c["id"], "nome": c["nome"], "tipo": c["tipo"], "aderencia": aderencia,
                      "motivo": r.motivo, "url_inscricao": c["url_inscricao"] or c["site"],
                      "inscricao_fecha": c["inscricao_fecha"].isoformat() if c["inscricao_fecha"] else None,
                      "ticket_texto": c["ticket_texto"]})
    return itens


@rota.get("/relatorios")
async def listar_relatorios(usuario: Usuario = Depends(usuario_atual)):
    return await buscar_todos(
        """select id, modo, titulo, status, criado_em from relatorios
            where usuario_id = %s order by criado_em desc limit 100""",
        (usuario.id,),
    )


@rota.get("/relatorios/{relatorio_id}")
async def ver_relatorio(relatorio_id: int, usuario: Usuario = Depends(usuario_atual)):
    rel = await buscar_um(
        """select id, modo, titulo, entrada, conteudo, estruturado, fontes, status, modelo, criado_em
             from relatorios where id = %s and usuario_id = %s""",
        (relatorio_id, usuario.id),
    )
    if rel is None:
        raise HTTPException(404, "Relatório não encontrado")
    return rel


@rota.get("/oportunidades")
async def oportunidades(usuario: Usuario = Depends(usuario_atual)):
    """Prazos de inscrição: primeiro os recomendados ao usuário, depois os gerais."""
    minhas = await buscar_todos(
        """select distinct on (i.id) i.id, i.nome, i.tipo, i.inscricao_fecha, i.ticket_texto,
                  coalesce(i.url_inscricao, i.site) as link, r.aderencia, r.salvo
             from recomendacoes r join investidores i on i.id = r.investidor_id
            where r.usuario_id = %s and (i.inscricao_fecha is null or i.inscricao_fecha >= current_date)
            order by i.id, r.aderencia desc""",
        (usuario.id,),
    )
    minhas.sort(key=lambda x: (x["inscricao_fecha"] is None, x["inscricao_fecha"] or "", -x["aderencia"]))
    abertas = await buscar_todos(
        """select id, nome, tipo, inscricao_fecha, ticket_texto, paises, coalesce(url_inscricao, site) as link
             from investidores
            where inscricao_fecha between current_date and current_date + 45
            order by inscricao_fecha limit 30""",
    )
    return {"recomendadas": minhas, "abertas": abertas}


@rota.post("/recomendacoes/{investidor_id}/salvar")
async def salvar_recomendacao(investidor_id: int, usuario: Usuario = Depends(usuario_atual)):
    linha = await buscar_um(
        """update recomendacoes set salvo = not salvo
            where usuario_id = %s and investidor_id = %s returning salvo""",
        (usuario.id, investidor_id),
    )
    if linha is None:
        raise HTTPException(404, "Recomendação não encontrada")
    return linha
