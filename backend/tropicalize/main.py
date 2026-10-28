"""API do Tropicalize (FastAPI). O site/app (web/) consome estas rotas."""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .auth import Usuario, admin_atual
from .db import abrir_pool, buscar_todos, fechar_pool
from .nuvc import nuvc
from .rotas import analises, noticias, push
from .servicos import noticias as servico_noticias

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    await abrir_pool()
    yield
    await nuvc.fechar()
    await fechar_pool()


app = FastAPI(title="Tropicalize API", lifespan=ciclo_de_vida)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGENS_PERMITIDAS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(analises.rota)
app.include_router(noticias.rota)
app.include_router(push.rota)


@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"ok": True, "nuvc": nuvc.ativo, "modelo": config.MODELO_PROFUNDO}


@app.post("/api/admin/coletar-noticias")
async def coletar_noticias(_: Usuario = Depends(admin_atual)):
    return {"novas": await servico_noticias.coletar()}


@app.get("/api/admin/newsletter")
async def newsletters(_: Usuario = Depends(admin_atual)):
    return await buscar_todos(
        "select id, newsletter_semana, texto, status from posts_sociais "
        "where rede = 'newsletter' order by newsletter_semana desc limit 12")


@app.post("/api/admin/newsletter")
async def gerar_newsletter(_: Usuario = Depends(admin_atual)):
    return {"id": await servico_noticias.gerar_newsletter_semanal()}
