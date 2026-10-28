"""Busca híbrida: filtros exatos no Postgres + similaridade semântica (pgvector)."""
from .db import buscar_todos, vetor
from .embeddings import embed_consulta

FAIXAS = {"ate_5k", "5k_50k", "acima_50k"}


async def startups_parecidas(texto: str, limite: int = 10, *, fora_do_brasil: bool = False) -> list[dict]:
    """Benchmarks: startups cuja descrição mais se aproxima do texto."""
    emb = vetor(await embed_consulta(texto))
    filtro = "and not ('Brazil' = any(paises) or 'Brasil' = any(paises))" if fora_do_brasil else ""
    return await buscar_todos(
        f"""
        select nome, descricao, setores, paises, lote, status, site, fonte,
               1 - (embedding <=> %(emb)s::vector) as similaridade
          from startups
         where embedding is not null {filtro}
         order by embedding <=> %(emb)s::vector
         limit %(limite)s
        """,
        {"emb": emb, "limite": limite},
    )


async def investidores_compativeis(
    texto: str,
    *,
    paises: list[str] | None = None,
    estagio: str | None = None,
    captacao_usd: float | None = None,
    tipos: list[str] | None = None,
    so_inscricoes_abertas: bool = False,
    limite: int = 30,
) -> list[dict]:
    """Fundos/aceleradoras que passam nos filtros, ordenados pela proximidade da tese.

    Campos desconhecidos (sem estágio, sem ticket) não eliminam o candidato: a base
    pública é incompleta e é melhor o modelo avaliar do que perder uma boa opção.
    """
    emb = vetor(await embed_consulta(texto))
    condicoes = ["embedding is not null", "(inscricao_fecha is null or inscricao_fecha >= current_date)"]
    params: dict = {"emb": emb, "limite": limite}
    if paises:
        condicoes.append("(cardinality(paises) = 0 or paises && %(paises)s or 'Global' = any(paises))")
        params["paises"] = paises
    if estagio:
        condicoes.append("(cardinality(estagios) = 0 or %(estagio)s = any(estagios))")
        params["estagio"] = estagio
    if captacao_usd:
        condicoes.append("(ticket_max_usd is null or ticket_max_usd >= %(cap)s * 0.1)")
        condicoes.append("(ticket_min_usd is null or ticket_min_usd <= %(cap)s)")
        params["cap"] = captacao_usd
    if tipos:
        condicoes.append("tipo = any(%(tipos)s)")
        params["tipos"] = tipos
    if so_inscricoes_abertas:
        condicoes.append("inscricao_fecha is not null")
    return await buscar_todos(
        f"""
        select id, tipo, nome, tese, setores, estagios, paises, cidade, ticket_texto,
               ticket_min_usd, ticket_max_usd, equity_texto, nao_diluitivo, site,
               url_inscricao, inscricao_fecha, inscricao_texto, verificado, fonte,
               1 - (embedding <=> %(emb)s::vector) as similaridade
          from investidores
         where {' and '.join(condicoes)}
         order by embedding <=> %(emb)s::vector
         limit %(limite)s
        """,
        params,
    )


async def ferramentas_ate(faixa: str) -> list[dict]:
    """Ferramentas do catálogo que cabem no orçamento (inclui as faixas mais baratas)."""
    ordem = ["ate_5k", "5k_50k", "acima_50k"]
    if faixa not in FAIXAS:
        faixa = "acima_50k"
    permitidas = ordem[: ordem.index(faixa) + 1]
    return await buscar_todos(
        """
        select nome, categoria, descricao, preco_texto, faixa, coalesce(link_afiliado, site) as link
          from ferramentas
         where faixa = any(%s)
         order by categoria, nome
        """,
        (permitidas,),
    )
