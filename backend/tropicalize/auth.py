"""Autenticação com o Supabase Auth e cota mensal de análises."""
import time
from dataclasses import dataclass

import httpx
from fastapi import Depends, Header, HTTPException

from . import config
from .db import buscar_um, executar

_cache: dict[str, tuple[float, "Usuario"]] = {}
CACHE_SEGUNDOS = 300


@dataclass(frozen=True)
class Usuario:
    id: str
    email: str
    plano: str

    @property
    def admin(self) -> bool:
        return self.plano == "admin"


async def _validar_token(token: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as http:
        r = await http.get(f"{config.SUPABASE_URL}/auth/v1/user",
                           headers={"Authorization": f"Bearer {token}", "apikey": config.SUPABASE_ANON_KEY})
    if r.status_code != 200:
        raise HTTPException(401, "Sessão inválida ou expirada. Entre de novo.")
    return r.json()


async def usuario_atual(authorization: str = Header("")) -> Usuario:
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Faça login para continuar.")
    agora = time.monotonic()
    em_cache = _cache.get(token)
    if em_cache and em_cache[0] > agora:
        return em_cache[1]

    dados = await _validar_token(token)
    email = (dados.get("email") or "").lower()
    plano_inicial = "admin" if email in config.ADMIN_EMAILS else "gratis"
    perfil = await buscar_um(
        """
        insert into perfis (usuario_id, email, plano) values (%s, %s, %s)
        on conflict (usuario_id) do update
           set email = excluded.email,
               plano = case when excluded.plano = 'admin' then 'admin' else perfis.plano end
        returning plano
        """,
        (dados["id"], email, plano_inicial),
    )
    usuario = Usuario(id=dados["id"], email=email, plano=perfil["plano"])
    _cache[token] = (agora + CACHE_SEGUNDOS, usuario)
    if len(_cache) > 5000:
        _cache.clear()
    return usuario


async def admin_atual(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    if not usuario.admin:
        raise HTTPException(403, "Acesso restrito à equipe.")
    return usuario


async def consumir_cota(usuario: Usuario) -> int:
    """Conta uma análise no mês; devolve quantas restam ou recusa se acabou."""
    limite = config.COTA_MENSAL.get(usuario.plano, 0)
    linha = await buscar_um(
        """
        insert into uso_mensal (usuario_id, mes, analises)
        values (%(u)s, date_trunc('month', now())::date, 1)
        on conflict (usuario_id, mes) do update set analises = uso_mensal.analises + 1
         where uso_mensal.analises < %(limite)s
        returning analises
        """,
        {"u": usuario.id, "limite": limite},
    )
    if linha is None:
        raise HTTPException(429, f"Você usou as {limite} análises do mês no plano {usuario.plano}.")
    return limite - linha["analises"]


async def devolver_cota(usuario: Usuario) -> None:
    """Desfaz o consumo quando a análise falha antes de gerar conteúdo."""
    await executar(
        "update uso_mensal set analises = greatest(analises - 1, 0) "
        "where usuario_id = %s and mes = date_trunc('month', now())::date",
        (usuario.id,),
    )
