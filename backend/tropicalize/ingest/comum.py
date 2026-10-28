"""Gravação em lote na base + geração dos embeddings pendentes."""
import logging

from ..db import buscar_todos, conexao, vetor
from ..embeddings import embed_documentos

log = logging.getLogger(__name__)

CAMPOS_STARTUP = ("fonte", "fonte_id", "nome", "descricao", "descricao_longa", "setores", "tags", "paises",
                  "estagio", "status", "lote", "site", "url_fonte")
CAMPOS_INVESTIDOR = ("fonte", "fonte_id", "tipo", "nome", "tese", "setores", "estagios", "paises", "cidade",
                     "ticket_min_usd", "ticket_max_usd", "ticket_texto", "equity_texto", "nao_diluitivo", "site",
                     "url_inscricao", "inscricao_abre", "inscricao_fecha", "inscricao_texto", "url_fonte")
CAMPOS_LISTA = {"setores", "tags", "paises", "estagios"}
# Se algum destes mudar, o embedding é refeito
CAMPOS_TEXTO_STARTUP = ("nome", "descricao", "setores")
CAMPOS_TEXTO_INVESTIDOR = ("nome", "tese", "setores", "estagios", "paises")


def _upsert_sql(tabela: str, campos: tuple, campos_texto: tuple) -> str:
    colunas = ", ".join(campos)
    valores = ", ".join(f"%({c})s" for c in campos)
    # Valor vazio na nova coleta não apaga o que já existe (ex.: dados de enriquecimento)
    atualiza = ", ".join(
        f"{c} = case when cardinality(excluded.{c}) = 0 then {tabela}.{c} else excluded.{c} end"
        if c in CAMPOS_LISTA else f"{c} = coalesce(excluded.{c}, {tabela}.{c})"
        for c in campos if c not in ("fonte", "fonte_id"))
    mudou = " or ".join(f"{tabela}.{c} is distinct from excluded.{c}" for c in campos_texto)
    return f"""
        insert into {tabela} ({colunas}) values ({valores})
        on conflict (fonte, fonte_id) do update set {atualiza},
            embedding = case when {mudou} then null else {tabela}.embedding end,
            atualizado_em = now()
    """


async def _gravar(tabela: str, campos: tuple, campos_texto: tuple, linhas: list[dict]) -> int:
    sql = _upsert_sql(tabela, campos, campos_texto)
    async with conexao() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(sql, [{c: l.get(c) for c in campos} for l in linhas])
    return len(linhas)


async def gravar_startups(linhas: list[dict]) -> int:
    for l in linhas:
        l.setdefault("setores", []), l.setdefault("tags", []), l.setdefault("paises", [])
    return await _gravar("startups", CAMPOS_STARTUP, CAMPOS_TEXTO_STARTUP, linhas)


async def gravar_investidores(linhas: list[dict]) -> int:
    for l in linhas:
        l.setdefault("setores", []), l.setdefault("estagios", []), l.setdefault("paises", [])
        l.setdefault("nao_diluitivo", False)
    return await _gravar("investidores", CAMPOS_INVESTIDOR, CAMPOS_TEXTO_INVESTIDOR, linhas)


async def gerar_embeddings_pendentes(lote: int = 500) -> int:
    """Calcula o embedding de toda linha nova ou alterada (embedding nulo)."""
    total = 0
    consultas = {
        "startups": "select id, nome, concat_ws('. ', descricao, descricao_longa, array_to_string(setores, ', ')) as texto "
                    "from startups where embedding is null limit %s",
        "investidores": "select id, nome, concat_ws('. ', tipo, tese, 'Setores: ' || array_to_string(setores, ', '), "
                        "'Estágios: ' || array_to_string(estagios, ', '), 'Países: ' || array_to_string(paises, ', ')) as texto "
                        "from investidores where embedding is null limit %s",
    }
    for tabela, sql in consultas.items():
        while linhas := await buscar_todos(sql, (lote,)):
            vetores = await embed_documentos([(l["nome"], l["texto"][:6000]) for l in linhas])
            async with conexao() as conn:
                async with conn.cursor() as cur:
                    await cur.executemany(f"update {tabela} set embedding = %s::vector where id = %s",
                                          [(vetor(v), l["id"]) for v, l in zip(vetores, linhas)])
            total += len(linhas)
            log.info("%s: %s embeddings gerados", tabela, total)
    return total
