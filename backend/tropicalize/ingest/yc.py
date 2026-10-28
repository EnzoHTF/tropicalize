"""Importa as startups da Y Combinator (all.json do yc-oss) como benchmarks."""
import json
from pathlib import Path

from .comum import gravar_startups


async def importar(caminho: str | Path) -> int:
    with open(caminho, encoding="utf-8") as f:
        startups = json.load(f)
    linhas = []
    for s in startups:
        descricao = (s.get("one_liner") or s.get("long_description") or "").strip()
        if not descricao or not s.get("name"):
            continue
        linhas.append({
            "fonte": "yc",
            "fonte_id": str(s.get("id") or s.get("slug")),
            "nome": s["name"],
            "descricao": descricao,
            "descricao_longa": (s.get("long_description") or "").strip() or None,
            "setores": [i for i in (s.get("industries") or []) if i],
            "tags": [t for t in (s.get("tags") or []) if t],
            "paises": [r for r in (s.get("regions") or []) if r not in ("Remote", "Partly Remote")],
            "estagio": s.get("stage"),
            "status": s.get("status"),
            "lote": s.get("batch"),
            "site": s.get("website"),
            "url_fonte": s.get("url"),
        })
    return await gravar_startups(linhas)
