"""Sobe a API localmente: python rodar_local.py

No Windows, o psycopg assíncrono exige o SelectorEventLoop, mas o uvicorn escolhe o
ProactorEventLoop por conta própria. Aqui o loop é criado antes e o uvicorn só o usa.
Nesse modo o Windows não abre subprocessos, então as ferramentas do NUVC ficam
desligadas localmente (no Linux/Modal funcionam normalmente).
"""
import asyncio
import os
import sys

import uvicorn

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        os.environ["NUVC_API_KEY"] = ""  # o load_dotenv não sobrescreve variáveis já definidas
    from tropicalize.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), loop="none")
    asyncio.run(uvicorn.Server(config).serve())
