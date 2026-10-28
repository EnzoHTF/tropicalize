"""Blog de notícias: leitura pública e curadoria pelo admin."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import Usuario, admin_atual
from ..db import buscar_todos, buscar_um
from ..servicos import redes_sociais

rota = APIRouter(prefix="/api")

CAMPOS_LISTA = "id, slug, titulo, resumo, categoria, tags, fonte_nome, imagem_url, publicado_em"


@rota.get("/noticias")
async def listar(categoria: Literal["brasil", "mundo"] | None = None, pagina: int = 1, tag: str | None = None):
    pagina = max(pagina, 1)
    condicoes, params = ["status = 'publicado'"], {"lim": 20, "off": (pagina - 1) * 20}
    if categoria:
        condicoes.append("categoria = %(cat)s")
        params["cat"] = categoria
    if tag:
        condicoes.append("%(tag)s = any(tags)")
        params["tag"] = tag
    return await buscar_todos(
        f"select {CAMPOS_LISTA} from noticias where {' and '.join(condicoes)} "
        "order by publicado_em desc limit %(lim)s offset %(off)s",
        params,
    )


@rota.get("/noticias/{slug}")
async def ver(slug: str):
    n = await buscar_um(
        f"select {CAMPOS_LISTA}, por_que_importa, fonte_url, publicado_fonte_em from noticias "
        "where slug = %s and status = 'publicado'",
        (slug,),
    )
    if n is None:
        raise HTTPException(404, "Notícia não encontrada")
    return n


# --- Curadoria (admin) ---

@rota.get("/admin/noticias")
async def fila(status: Literal["rascunho", "publicado", "descartado"] = "rascunho", _: Usuario = Depends(admin_atual)):
    noticias = await buscar_todos(
        f"select {CAMPOS_LISTA}, por_que_importa, fonte_url, status, criado_em from noticias "
        "where status = %s order by criado_em desc limit 100",
        (status,),
    )
    if noticias:
        posts = await buscar_todos(
            "select noticia_id, rede, texto, status from posts_sociais where noticia_id = any(%s)",
            ([n["id"] for n in noticias],),
        )
        por_noticia: dict[int, list] = {}
        for p in posts:
            por_noticia.setdefault(p["noticia_id"], []).append(p)
        for n in noticias:
            n["posts"] = por_noticia.get(n["id"], [])
    return noticias


class Edicao(BaseModel):
    titulo: str | None = Field(None, max_length=200)
    resumo: str | None = Field(None, max_length=5000)
    por_que_importa: str | None = Field(None, max_length=2000)
    tags: list[str] | None = None
    posts: dict[str, str] | None = None  # rede -> texto


@rota.put("/admin/noticias/{noticia_id}")
async def editar(noticia_id: int, edicao: Edicao, _: Usuario = Depends(admin_atual)):
    campos = edicao.model_dump(exclude_none=True, exclude={"posts"})
    if campos:
        sets = ", ".join(f"{c} = %({c})s" for c in campos)
        await buscar_um(f"update noticias set {sets} where id = %(id)s returning id", {**campos, "id": noticia_id})
    for rede, texto in (edicao.posts or {}).items():
        await buscar_um("update posts_sociais set texto = %s where noticia_id = %s and rede = %s returning id",
                        (texto, noticia_id, rede))
    return {"ok": True}


@rota.post("/admin/noticias/{noticia_id}/publicar")
async def publicar(noticia_id: int, _: Usuario = Depends(admin_atual)):
    n = await buscar_um(
        """update noticias set status = 'publicado', publicado_em = coalesce(publicado_em, now())
            where id = %s returning id, slug, titulo""",
        (noticia_id,),
    )
    if n is None:
        raise HTTPException(404, "Notícia não encontrada")
    enviados = await redes_sociais.enviar_posts_da_noticia(noticia_id)
    return {"ok": True, "posts_enviados": enviados}


@rota.post("/admin/noticias/{noticia_id}/descartar")
async def descartar(noticia_id: int, _: Usuario = Depends(admin_atual)):
    await buscar_um("update noticias set status = 'descartado' where id = %s returning id", (noticia_id,))
    return {"ok": True}
