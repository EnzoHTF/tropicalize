"""Importa as listas curadas de dados/ (investidores iniciais e catálogo de ferramentas)."""
import csv

from .. import config
from ..db import conexao
from .comum import gravar_investidores

PASTA = config.BASE_DIR / "dados"


def _ler(nome: str) -> list[dict]:
    with open(PASTA / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in (valor or "").split("|") if v.strip()]


async def importar_investidores() -> int:
    linhas = []
    for r in _ler("investidores_sementes.csv"):
        linhas.append({
            "fonte": "semente", "fonte_id": r["nome"].lower(), "tipo": r["tipo"], "nome": r["nome"],
            "tese": r["tese"] or None, "paises": _lista(r["paises"]), "cidade": r["cidade"] or None,
            "estagios": _lista(r["estagios"]), "nao_diluitivo": r["nao_diluitivo"] == "true",
            "site": r["site"] or None,
        })
    return await gravar_investidores(linhas)


async def importar_ferramentas() -> int:
    linhas = _ler("ferramentas.csv")
    async with conexao() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                """insert into ferramentas (nome, categoria, faixa, site, preco_texto, descricao)
                   values (%(nome)s, %(categoria)s, %(faixa)s, %(site)s, %(preco_texto)s, %(descricao)s)
                   on conflict (nome) do update set categoria = excluded.categoria, faixa = excluded.faixa,
                       site = excluded.site, preco_texto = excluded.preco_texto, descricao = excluded.descricao,
                       atualizado_em = now()""",
                linhas,
            )
    return len(linhas)
