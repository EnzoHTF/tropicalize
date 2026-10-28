"""Coleta programas (aceleradoras, incubadoras, editais) e investidores do F6S via Apify.

Ator: jungle_synthesizer/f6s-accelerator-scraper (cobrança por registro). Rode por país
para ter o filtro de geografia preenchido também nos investidores.
"""
import logging
import re
from datetime import date

from apify_client import ApifyClientAsync

from .. import config
from .comum import gravar_investidores

log = logging.getLogger(__name__)

PAISES_PADRAO = ["Brazil", "Portugal", "United States", "Mexico", "Argentina", "Chile", "Colombia",
                 "United Kingdom", "Spain", "Germany", "France", "Canada", "Israel", "Singapore"]

_MULT = {"k": 1e3, "m": 1e6, "mm": 1e6, "b": 1e9}
_TIPOS_POR_PALAVRA = [
    (("accelerat", "acelera"), "aceleradora"),
    (("incubat", "incuba"), "incubadora"),
    (("grant", "edital", "subven", "fund for", "prize"), "governo"),
    (("angel", "anjo"), "anjos"),
]


def valores_usd(texto: str | None) -> tuple[float | None, float | None]:
    """'$100k' -> (100000, 100000); '$50k - $250k' -> (50000, 250000). Só reconhece dólar."""
    if not texto or "$" not in texto or "R$" in texto:
        return None, None
    numeros = [float(n.replace(",", "")) * _MULT.get(m.lower(), 1)
               for n, m in re.findall(r"\$\s*([\d.,]+)\s*(mm|[kmb])?", texto, re.I)]
    if not numeros:
        return None, None
    return min(numeros), max(numeros)


def _tipo_programa(nome: str, descricao: str) -> str:
    alvo = f"{nome} {descricao}".lower()
    for palavras, tipo in _TIPOS_POR_PALAVRA:
        if any(p in alvo for p in palavras):
            return tipo
    return "programa"


def _setores(texto: str | None) -> list[str]:
    texto = (texto or "").removeprefix("Funds Startups in").strip()
    return [s.strip() for s in texto.split(",") if s.strip()]


def _data(iso: str | None) -> date | None:
    try:
        return date.fromisoformat(iso) if iso else None
    except ValueError:
        return None


def _programa(item: dict) -> dict:
    minimo, maximo = valores_usd(item.get("program_investment_amount"))
    nome = item["program_name"]
    return {
        "fonte": "f6s", "fonte_id": item["program_slug"],
        "tipo": _tipo_programa(nome, item.get("program_description") or ""),
        "nome": nome, "tese": item.get("program_description"),
        "setores": _setores(item.get("program_sector")),
        "paises": [item["program_country"]] if item.get("program_country") else [],
        "cidade": item.get("program_city") or None,
        "ticket_min_usd": minimo, "ticket_max_usd": maximo,
        "ticket_texto": item.get("program_investment_amount") or None,
        "equity_texto": item.get("program_equity_taken") or None,
        "site": item.get("program_website") or None,
        "url_inscricao": item.get("program_application_url") or None,
        "inscricao_fecha": _data(item.get("program_application_deadline_iso")),
        "inscricao_texto": item.get("program_application_deadline") or None,
        "url_fonte": item.get("program_url"),
    }


def _investidor(item: dict, pais: str | None) -> dict:
    minimo, maximo = valores_usd(item.get("investor_check_size"))
    return {
        "fonte": "f6s", "fonte_id": item["investor_slug"], "tipo": "fundo_vc",
        "nome": item["investor_name"], "tese": item.get("investor_investment_sector"),
        "setores": _setores(item.get("investor_investment_sector")),
        "paises": [pais] if pais else [],
        "ticket_min_usd": minimo, "ticket_max_usd": maximo,
        "ticket_texto": item.get("investor_check_size") or None,
        "url_fonte": item.get("investor_url"),
    }


async def _rodar(cliente: ApifyClientAsync, entrada: dict) -> list[dict]:
    execucao = await cliente.actor(config.APIFY_ATOR_F6S).call(run_input=entrada)
    if execucao is None:
        return []
    return [item async for item in cliente.dataset(execucao.default_dataset_id).iterate_items()]


async def coletar(paises: list[str] | None = None, max_por_pais: int = 0) -> int:
    """Coleta programas e investidores de cada país (max_por_pais=0 é ilimitado)."""
    if not config.APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN não configurado")
    cliente = ApifyClientAsync(config.APIFY_TOKEN)
    total = 0
    for pais in paises or PAISES_PADRAO:
        for tipo in ("programs", "investors"):
            entrada = {"entityType": tipo, "country": pais, "maxItems": max_por_pais}
            if tipo == "programs":
                entrada["fetchDetails"] = True
            try:
                itens = await _rodar(cliente, entrada)
            except Exception:  # noqa: BLE001 - um país com problema não derruba a coleta
                log.exception("F6S %s/%s falhou", pais, tipo)
                continue
            if tipo == "programs":
                linhas = [_programa(i) for i in itens if i.get("program_slug") and i.get("program_name")]
            else:
                linhas = [_investidor(i, pais) for i in itens if i.get("investor_slug") and i.get("investor_name")]
            total += await gravar_investidores(linhas)
            log.info("F6S %s/%s: %s registros", pais, tipo, len(linhas))
    return total
