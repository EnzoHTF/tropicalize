import modal

app = modal.App("tropicalize-modal")


def baixar_modelo_embeddings():
    # Baixa o modelo ONNX na construção da imagem, e não a cada cold start
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    DefaultEmbeddingFunction()(["aquecimento"])


web_image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install(
        "gradio==6.30.0",
        "chromadb==1.5.9",
        "openai==3.36.1",
        "deep-translator==1.11.4",
        "fastapi==0.159.1",
    )
    .run_function(baixar_modelo_embeddings)
    .add_local_dir("chroma_db", remote_path="/root/chroma_db")
    .add_local_dir("static", remote_path="/root/static")
    .add_local_python_source("app")
)


@app.function(
    image=web_image,
    secrets=[modal.Secret.from_name("groq-secret")],
    timeout=600,
    max_containers=1,
    scaledown_window=60 * 20,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def ui():
    from app import app as web_app
    return web_app
