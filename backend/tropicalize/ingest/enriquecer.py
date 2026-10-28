"""Completa fundos/aceleradoras com dados públicos pesquisados na web.

Para cada registro não verificado, o Claude pesquisa o site oficial e notícias e
devolve tese, setores, estágios, ticket, link e prazo de inscrição, sempre com a
URL de onde tirou o dado. Campos sem fonte ficam vazios.
"""
import logging
from datetime import date

from pydantic import BaseModel, Field

from .. import config, llm
from ..db import buscar_todos, executar

log = logging.getLogger(__name__)

PESQUISA = """Pesquise na web informações públicas e atuais sobre o investidor/programa abaixo. \
Priorize o site oficial. Responda em português com: site oficial; tese e foco; setores; estágios \
em que investe; países/regiões onde investe; tamanho de cheque ou valor oferecido; se é capital \
não diluitivo; link de inscrição; e prazo da próxima inscrição se houver. Cite a URL de cada dado. \
Se não encontrar um dado, diga que não encontrou. Não invente."""


class DadosInvestidor(BaseModel):
    encontrado: bool = Field(description="True se a pesquisa achou a organização com segurança")
    site: str | None = None
    tese: str | None = Field(None, description="1 a 3 frases em português")
    setores: list[str] = Field(default_factory=list)
    estagios: list[str] = Field(default_factory=list,
                                description="Somente: pre_seed, seed, series_a, series_b, growth")
    paises: list[str] = Field(default_factory=list,
                              description="Nomes em inglês (ex.: Brazil), 'Latin America' ou 'Global'")
    ticket_min_usd: float | None = None
    ticket_max_usd: float | None = None
    ticket_texto: str | None = Field(None, description="Como aparece na fonte, ex.: 'R$ 500 mil a R$ 2 mi'")
    nao_diluitivo: bool | None = None
    url_inscricao: str | None = None
    inscricao_fecha: date | None = None
    url_fonte: str | None = Field(None, description="Principal URL usada")


ESTAGIOS = {"pre_seed", "seed", "series_a", "series_b", "growth"}


async def enriquecer(limite: int = 50) -> int:
    pendentes = await buscar_todos(
        """select id, tipo, nome, cidade, paises, site from investidores
            where not verificado and fonte in ('semente', 'f6s')
            order by (fonte = 'semente') desc, atualizado_em limit %s""",
        (limite,),
    )
    feitos = 0
    for inv in pendentes:
        alvo = f"{inv['nome']} ({inv['tipo']}; {inv['cidade'] or ''} {', '.join(inv['paises'])}; site: {inv['site'] or '?'})"
        try:
            pesquisa = await llm.completar(PESQUISA, alvo, modelo=config.MODELO_PESQUISA, usar_web=True)
        except RuntimeError:
            log.exception("Pesquisa falhou para %s", inv["nome"])
            continue
        dados = await llm.estruturar("Extraia os dados do investidor descritos no texto.", pesquisa, DadosInvestidor)
        if dados is None or not dados.encontrado:
            await executar("update investidores set verificado = true, atualizado_em = now() where id = %s",
                           (inv["id"],))  # não tenta de novo toda semana
            continue
        await executar(
            """update investidores set
                   site = coalesce(%(site)s, site), tese = coalesce(%(tese)s, tese),
                   setores = case when cardinality(%(setores)s::text[]) > 0 then %(setores)s else setores end,
                   estagios = case when cardinality(%(estagios)s::text[]) > 0 then %(estagios)s else estagios end,
                   paises = case when cardinality(%(paises)s::text[]) > 0 then %(paises)s else paises end,
                   ticket_min_usd = coalesce(%(tmin)s, ticket_min_usd), ticket_max_usd = coalesce(%(tmax)s, ticket_max_usd),
                   ticket_texto = coalesce(%(ttxt)s, ticket_texto), nao_diluitivo = coalesce(%(nd)s, nao_diluitivo),
                   url_inscricao = coalesce(%(insc)s, url_inscricao), inscricao_fecha = coalesce(%(fecha)s, inscricao_fecha),
                   url_fonte = coalesce(%(fonte)s, url_fonte), verificado = true, embedding = null, atualizado_em = now()
                where id = %(id)s""",
            {"id": inv["id"], "site": dados.site, "tese": dados.tese, "setores": dados.setores,
             "estagios": [e for e in dados.estagios if e in ESTAGIOS], "paises": dados.paises,
             "tmin": dados.ticket_min_usd, "tmax": dados.ticket_max_usd, "ttxt": dados.ticket_texto,
             "nd": dados.nao_diluitivo, "insc": dados.url_inscricao, "fecha": dados.inscricao_fecha,
             "fonte": dados.url_fonte},
        )
        feitos += 1
        log.info("Enriquecido: %s", inv["nome"])
    return feitos
