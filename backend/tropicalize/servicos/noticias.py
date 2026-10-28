"""Coleta de notícias por RSS → resumo próprio pela IA → rascunho para aprovação.

Direitos autorais: a IA recebe só o título e o resumo do feed e escreve um texto próprio
curto, sempre com link para a matéria original. Nada vai ao ar sem aprovação humana.
"""
import asyncio
import hashlib
import logging
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from time import mktime
from typing import Literal

import feedparser
import httpx
from pydantic import BaseModel, Field

from .. import config, llm
from ..db import buscar_todos, buscar_um, executar

log = logging.getLogger(__name__)

FONTES = [
    # (nome, url, categoria)
    ("Startupi", "https://startupi.com.br/feed/", "brasil"),
    ("Startups.com.br", "https://startups.com.br/feed/", "brasil"),
    ("NeoFeed", "https://neofeed.com.br/feed/", "brasil"),
    ("Brazil Journal", "https://braziljournal.com/feed/", "brasil"),
    ("InfoMoney", "https://www.infomoney.com.br/feed/", "brasil"),
    ("Exame", "https://exame.com/feed/", "brasil"),
    ("TechCrunch Venture", "https://techcrunch.com/category/venture/feed/", "mundo"),
    ("TechCrunch", "https://techcrunch.com/feed/", "mundo"),
    ("Crunchbase News", "https://news.crunchbase.com/feed/", "mundo"),
    ("Sifted", "https://sifted.eu/feed", "mundo"),
    ("Rest of World", "https://restofworld.org/feed/latest/", "mundo"),
]
MAX_POR_EXECUCAO = 40
IDADE_MAXIMA = timedelta(days=3)
AGENTE = "Mozilla/5.0 (compatible; TropicalizeBot/1.0; +https://tropicalize.app)"


class PostsRedes(BaseModel):
    instagram: str = Field(description="Legenda com até 5 hashtags, sem link (link na bio)")
    linkedin: str = Field(description="Post profissional de 3 a 5 parágrafos curtos")
    x: str = Field(description="Até 250 caracteres")
    threads: str = Field(description="Até 450 caracteres, tom de conversa")


class NoticiaProcessada(BaseModel):
    relevante: bool = Field(description="True só se for sobre startups, venture capital, inovação ou negócios")
    titulo: str = Field(description="Título próprio em português, até 90 caracteres")
    resumo: str = Field(description="2 a 3 parágrafos curtos em português com palavras próprias, sem copiar a fonte")
    por_que_importa: str = Field(description="1 parágrafo: o que isso significa para empreendedores brasileiros")
    tags: list[str] = Field(description="2 a 5 tags em minúsculas, ex.: fintech, rodada, ia")
    posts: PostsRedes


INSTRUCAO = """Você é editor do blog do Tropicalize (negócios, startups e venture capital para \
empreendedores brasileiros). Avalie a notícia abaixo. Se for relevante, escreva em português \
do Brasil um título, um resumo com palavras próprias (não copie frases da fonte), por que isso \
importa para quem empreende no Brasil, tags e textos para cada rede social. Os posts devem \
convidar a ler o resumo completo no blog do Tropicalize. Não invente fatos além do que está no texto."""


def slugificar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:80] or "noticia"


def _limpar_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def _imagem(entrada) -> str | None:
    for chave in ("media_content", "media_thumbnail"):
        midias = entrada.get(chave) or []
        if midias and midias[0].get("url"):
            return midias[0]["url"]
    for link in entrada.get("links", []):
        if link.get("type", "").startswith("image/"):
            return link.get("href")
    return None


async def _ler_feed(http: httpx.AsyncClient, nome: str, url: str, categoria: str) -> list[dict]:
    try:
        r = await http.get(url)
        r.raise_for_status()
    except httpx.HTTPError as e:
        log.warning("Feed %s falhou: %s", nome, e)
        return []
    feed = feedparser.parse(r.content)
    agora = datetime.now(timezone.utc)
    itens = []
    for e in feed.entries:
        publicado = e.get("published_parsed") or e.get("updated_parsed")
        quando = datetime.fromtimestamp(mktime(publicado), timezone.utc) if publicado else agora
        if agora - quando > IDADE_MAXIMA or not e.get("link"):
            continue
        itens.append({"fonte_nome": nome, "fonte_url": e.link, "categoria": categoria,
                      "titulo_original": e.get("title", ""), "descricao": _limpar_html(e.get("summary", ""))[:1500],
                      "imagem_url": _imagem(e), "publicado_fonte_em": quando})
    return itens


async def coletar() -> int:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": AGENTE}) as http:
        lotes = await asyncio.gather(*(_ler_feed(http, *f) for f in FONTES))
    candidatos = [i for lote in lotes for i in lote]
    if not candidatos:
        return 0
    existentes = {r["fonte_url"] for r in await buscar_todos(
        "select fonte_url from noticias where fonte_url = any(%s)", ([c["fonte_url"] for c in candidatos],))}
    novos = [c for c in candidatos if c["fonte_url"] not in existentes]
    novos.sort(key=lambda c: c["publicado_fonte_em"], reverse=True)

    criadas = 0
    for item in novos[:MAX_POR_EXECUCAO]:
        texto = f"Fonte: {item['fonte_nome']}\nTítulo: {item['titulo_original']}\nResumo do feed: {item['descricao']}"
        proc = await llm.estruturar(INSTRUCAO, texto, NoticiaProcessada)
        if proc is None:
            continue
        if not proc.relevante:
            # Guarda como descartada para não reprocessar na próxima coleta
            await executar(
                """insert into noticias (slug, titulo, resumo, categoria, fonte_nome, fonte_url, status)
                   values (%s, %s, '', %s, %s, %s, 'descartado') on conflict do nothing""",
                (f"descartada-{hashlib.md5(item['fonte_url'].encode()).hexdigest()[:16]}", item["titulo_original"][:200] or "-",
                 item["categoria"], item["fonte_nome"], item["fonte_url"]))
            continue
        slug = await _slug_livre(slugificar(proc.titulo))
        linha = await buscar_um(
            """insert into noticias (slug, titulo, resumo, por_que_importa, categoria, tags, fonte_nome,
                                     fonte_url, imagem_url, publicado_fonte_em)
               values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               on conflict (fonte_url) do nothing returning id""",
            (slug, proc.titulo, proc.resumo, proc.por_que_importa, item["categoria"],
             [t.lower() for t in proc.tags][:5], item["fonte_nome"], item["fonte_url"],
             item["imagem_url"], item["publicado_fonte_em"]),
        )
        if linha is None:
            continue
        for rede, texto_post in proc.posts.model_dump().items():
            await executar("insert into posts_sociais (noticia_id, rede, texto) values (%s, %s, %s) on conflict do nothing",
                           (linha["id"], rede, texto_post))
        criadas += 1
    log.info("Notícias novas em rascunho: %s", criadas)
    return criadas


async def _slug_livre(base: str) -> str:
    slug, n = base, 2
    while await buscar_um("select 1 from noticias where slug = %s", (slug,)):
        slug, n = f"{base}-{n}", n + 1
    return slug


class Newsletter(BaseModel):
    assunto: str
    corpo_markdown: str


async def gerar_newsletter_semanal() -> int | None:
    """Monta a newsletter com as notícias publicadas nos últimos 7 dias (fica pendente para envio)."""
    noticias = await buscar_todos(
        """select titulo, resumo, por_que_importa, categoria, slug from noticias
            where status = 'publicado' and publicado_em > now() - interval '7 days'
            order by publicado_em desc limit 25""")
    if not noticias:
        return None
    lista = "\n\n".join(f"- [{n['categoria']}] {n['titulo']} ({config.SITE_URL}/blog/{n['slug']})\n"
                        f"  {n['resumo'][:600]}\n  Por que importa: {n['por_que_importa']}" for n in noticias)
    res = await llm.estruturar(
        "Escreva a newsletter semanal do Tropicalize em português do Brasil: um assunto chamativo e o corpo "
        "em markdown com abertura curta, as 5 a 8 notícias mais importantes (Brasil e mundo) com link para o "
        "blog, e um fechamento convidando a usar o Tropicalize para analisar ideias e encontrar investidores.",
        lista, Newsletter, modelo=config.MODELO_RAPIDO)
    if res is None:
        return None
    semana = date.today() - timedelta(days=date.today().weekday())
    linha = await buscar_um(
        """insert into posts_sociais (newsletter_semana, rede, texto) values (%s, 'newsletter', %s)
           on conflict (newsletter_semana, rede) do update set texto = excluded.texto returning id""",
        (semana, f"# {res.assunto}\n\n{res.corpo_markdown}"))
    return linha["id"]
