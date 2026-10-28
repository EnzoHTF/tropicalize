"""Chamadas ao Claude.

`gerar_relatorio` faz o loop agêntico com streaming: o modelo escreve o relatório, pode
pesquisar na web (ferramenta de servidor da Anthropic) e chamar as ferramentas do NUVC
(executadas aqui, via MCP). Cada passo vira um evento para o app mostrar em tempo real.
"""
import json
import logging
from collections.abc import AsyncIterator

import anthropic
import jsonschema
from pydantic import BaseModel

from . import config
from .nuvc import nuvc

log = logging.getLogger(__name__)

cliente = anthropic.AsyncAnthropic()

# Modelos que aceitam o fallback automático do servidor em caso de recusa dos classificadores
COM_FALLBACK = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
BETA_FALLBACK = "server-side-fallback-2026-07-01"
MAX_RODADAS = 12

BUSCA_WEB = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}


def _extras_modelo(modelo: str) -> dict:
    if modelo in COM_FALLBACK:
        return {"betas": [BETA_FALLBACK], "fallbacks": "default"}
    return {}


async def gerar_relatorio(
    system: str,
    mensagem: str,
    *,
    usar_web: bool = True,
    usar_nuvc: bool = True,
    modelo: str | None = None,
) -> AsyncIterator[dict]:
    """Gera eventos: status, texto, fonte e, no final, fim (com uso de tokens) ou erro."""
    modelo = modelo or config.MODELO_PROFUNDO
    ferramentas: list[dict] = []
    if usar_web:
        ferramentas.append(BUSCA_WEB)
    if usar_nuvc:
        ferramentas.extend(await nuvc.ferramentas())

    mensagens: list[dict] = [{"role": "user", "content": mensagem}]
    fontes_vistas: set[str] = set()
    tokens_entrada = tokens_saida = 0

    for _ in range(MAX_RODADAS):
        try:
            async with cliente.beta.messages.stream(
                model=modelo,
                max_tokens=64000,
                system=system,
                messages=mensagens,
                tools=ferramentas or anthropic.omit,
                output_config={"effort": config.ESFORCO_RELATORIO},
                cache_control={"type": "ephemeral"},
                **_extras_modelo(modelo),
            ) as stream:
                async for evento in stream:
                    if evento.type == "text":
                        yield {"tipo": "texto", "texto": evento.text}
                    elif evento.type == "content_block_stop":
                        for ev in _eventos_do_bloco(evento.content_block, fontes_vistas):
                            yield ev
                resposta = await stream.get_final_message()
        except ValueError:
            # JSON de ferramenta que o SDK não conseguiu interpretar: refaz a rodada
            log.warning("Entrada de ferramenta inválida no stream; repetindo a rodada")
            continue
        except anthropic.RateLimitError:
            yield {"tipo": "erro", "texto": "A IA está com muita demanda agora. Tente de novo em instantes."}
            return
        except anthropic.APIStatusError as e:
            log.error("Erro da API do Claude (%s): %s", e.status_code, e.message)
            yield {"tipo": "erro", "texto": "Não foi possível gerar a análise agora."}
            return
        except anthropic.APIConnectionError:
            yield {"tipo": "erro", "texto": "Falha de conexão com a IA. Tente de novo."}
            return

        tokens_entrada += resposta.usage.input_tokens or 0
        tokens_saida += resposta.usage.output_tokens or 0

        if resposta.stop_reason == "refusal":
            yield {"tipo": "erro", "texto": "A IA não conseguiu responder a este pedido. Reformule e tente de novo."}
            return

        mensagens.append({"role": "assistant", "content": resposta.content})

        if resposta.stop_reason == "pause_turn":
            continue  # a busca na web atingiu o limite da rodada; o reenvio retoma

        chamadas = [b for b in resposta.content if b.type == "tool_use"]
        if not chamadas:
            yield {"tipo": "fim", "modelo": resposta.model,
                   "tokens_entrada": tokens_entrada, "tokens_saida": tokens_saida}
            return
        if resposta.stop_reason == "max_tokens":
            yield {"tipo": "erro", "texto": "A resposta ficou longa demais e foi interrompida."}
            return

        resultados = []
        for chamada in chamadas:
            texto, erro = await _executar_ferramenta(chamada.name, chamada.input)
            resultados.append({"type": "tool_result", "tool_use_id": chamada.id,
                               "content": texto, "is_error": erro})
        mensagens.append({"role": "user", "content": resultados})

    yield {"tipo": "erro", "texto": "A análise usou passos demais e foi interrompida."}


def _eventos_do_bloco(bloco, fontes_vistas: set[str]) -> list[dict]:
    eventos = []
    if bloco.type == "server_tool_use" and bloco.name == "web_search":
        consulta = (bloco.input or {}).get("query", "")
        eventos.append({"tipo": "status", "texto": f"Pesquisando na web: {consulta}"})
    elif bloco.type == "web_search_tool_result" and isinstance(bloco.content, list):
        for r in bloco.content:
            if r.url not in fontes_vistas:
                fontes_vistas.add(r.url)
                eventos.append({"tipo": "fonte", "titulo": r.title, "url": r.url})
    elif bloco.type == "tool_use":
        eventos.append({"tipo": "status", "texto": f"Consultando NUVC: {bloco.name.removeprefix('nuvc_')}"})
    return eventos


async def _executar_ferramenta(nome: str, entrada) -> tuple[str, bool]:
    esquema = nuvc.esquema(nome)
    if esquema is None:
        return f"Ferramenta desconhecida: {nome}", True
    # Com eager_input_streaming o servidor não valida a entrada: validamos aqui
    if not isinstance(entrada, dict):
        return json.dumps({"INVALID_JSON": json.dumps(entrada, ensure_ascii=False)}), True
    try:
        jsonschema.validate(entrada, esquema)
    except jsonschema.ValidationError as e:
        return f"Entrada inválida para {nome}: {e.message}", True
    return await nuvc.chamar(nome, entrada)


async def estruturar(instrucao: str, texto: str, formato: type[BaseModel],
                     modelo: str | None = None) -> BaseModel | None:
    """Extrai dados estruturados de um texto (saída validada pelo schema do Pydantic)."""
    try:
        resposta = await cliente.messages.parse(
            model=modelo or config.MODELO_RAPIDO,
            max_tokens=16000,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": f"{instrucao}\n\n<texto>\n{texto}\n</texto>"}],
            output_format=formato,
        )
    except anthropic.APIError:
        log.exception("Falha ao estruturar saída")
        return None
    if resposta.stop_reason == "refusal":
        return None
    return resposta.parsed_output


async def completar(system: str, mensagem: str, *, modelo: str | None = None,
                    usar_web: bool = False) -> str:
    """Chamada simples (sem streaming para o usuário) que devolve só o texto final.
    Com busca na web, use um modelo que aceite web_search_20260209 (não o Haiku)."""
    partes = []
    async for ev in gerar_relatorio(system, mensagem, usar_web=usar_web, usar_nuvc=False,
                                    modelo=modelo or config.MODELO_RAPIDO):
        if ev["tipo"] == "texto":
            partes.append(ev["texto"])
        elif ev["tipo"] == "erro":
            raise RuntimeError(ev["texto"])
    return "".join(partes)
