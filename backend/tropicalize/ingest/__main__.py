"""Linha de comando das cargas e rotinas.

Exemplos (dentro de backend/):
    python -m tropicalize.ingest sementes
    python -m tropicalize.ingest yc ../all.json
    python -m tropicalize.ingest f6s Brazil Portugal
    python -m tropicalize.ingest enriquecer 50
    python -m tropicalize.ingest embeddings
    python -m tropicalize.ingest noticias
    python -m tropicalize.ingest newsletter
    python -m tropicalize.ingest alertas
"""
import asyncio
import logging
import sys

from ..db import fechar_pool


async def principal(comando: str, args: list[str]):
    from ..servicos import alertas, noticias
    from . import comum, enriquecer, f6s, sementes, yc

    if comando == "sementes":
        print("ferramentas:", await sementes.importar_ferramentas())
        print("investidores:", await sementes.importar_investidores())
    elif comando == "yc":
        print("startups:", await yc.importar(args[0] if args else "../all.json"))
    elif comando == "f6s":
        print("registros:", await f6s.coletar(args or None))
    elif comando == "enriquecer":
        print("enriquecidos:", await enriquecer.enriquecer(int(args[0]) if args else 50))
    elif comando == "embeddings":
        pass
    elif comando == "noticias":
        print("novas:", await noticias.coletar())
    elif comando == "newsletter":
        print("newsletter:", await noticias.gerar_newsletter_semanal())
    elif comando == "alertas":
        print("alertas:", await alertas.enviar_alertas_de_prazo())
    else:
        sys.exit(__doc__)
    if comando in ("sementes", "yc", "f6s", "enriquecer", "embeddings"):
        print("embeddings:", await comum.gerar_embeddings_pendentes())


async def rodar(comando: str, args: list[str]):
    try:
        await principal(comando, args)
    finally:
        await fechar_pool()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.platform == "win32":  # o psycopg assíncrono não funciona com o loop padrão do Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(rodar(sys.argv[1], sys.argv[2:]))
