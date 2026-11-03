"""Deploy do backend no Modal: API web + rotinas agendadas.

    modal secret create tropicalize --from-dotenv .env
    modal deploy modal_app.py
"""
import modal

app = modal.App("tropicalize")

imagem = (
    modal.Image.debian_slim(python_version="3.12")
    # Node para o servidor MCP do NUVC (stdio), instalado globalmente para subir rápido
    .apt_install("nodejs", "npm")
    .run_commands("npm install -g nuvc-mcp@1.4.1")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir("dados", remote_path="/root/dados")
    .add_local_python_source("tropicalize")
)
segredos = [modal.Secret.from_name("tropicalize")]
FUSO = "America/Sao_Paulo"


@app.function(image=imagem, secrets=segredos, timeout=900, scaledown_window=60 * 10)
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def api():
    from tropicalize.main import app as web_app
    return web_app


async def _rodar(comando: str, *args: str):
    from tropicalize.ingest.__main__ import rodar
    await rodar(comando, list(args))


@app.function(image=imagem, secrets=segredos, timeout=1800, schedule=modal.Cron("0 */3 * * *", timezone=FUSO))
async def coletar_noticias():
    await _rodar("noticias")


@app.function(image=imagem, secrets=segredos, timeout=600, schedule=modal.Cron("0 9 * * *", timezone=FUSO))
async def alertas_de_prazo():
    await _rodar("alertas")


@app.function(image=imagem, secrets=segredos, timeout=900, schedule=modal.Cron("0 7 * * 1", timezone=FUSO))
async def newsletter_semanal():
    await _rodar("newsletter")


@app.function(image=imagem, secrets=segredos, timeout=6 * 3600, schedule=modal.Cron("0 3 * * 0", timezone=FUSO))
async def atualizar_diretorios():
    """Domingo de madrugada: F6S (Apify) → enriquecimento na web → embeddings."""
    await _rodar("f6s")
    await _rodar("enriquecer", "100")
