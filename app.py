import os
# Otimização para máquinas fracas (evita que a IA trave o processador)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import threading
from pathlib import Path

import chromadb
import gradio as gr
from deep_translator import GoogleTranslator
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# ✅ Lê a chave da variável de ambiente
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

llm = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Carrega o banco em segundo plano: o servidor sobe na hora e a página inicial
# abre enquanto o modelo de embeddings (ONNX, sem torch) é preparado.
# O embedding padrão do Chroma é o mesmo all-MiniLM-L6-v2 usado no build_db.py.
_recursos = {}
_pronto = threading.Event()


def _carregar_banco():
    try:
        # Caminho relativo: o Chroma falha com acentos no caminho absoluto (ex.: "Usuário")
        client = chromadb.PersistentClient(path=os.path.relpath(BASE_DIR / "chroma_db"))
        collection = client.get_collection("yc_startups")
        collection.query(query_texts=["aquecimento"], n_results=1)
        _recursos["collection"] = collection
    except Exception as e:
        _recursos["erro"] = e
    finally:
        _pronto.set()


threading.Thread(target=_carregar_banco, daemon=True).start()


def responder_chat(mensagem, historico):
    if not mensagem or not mensagem.strip():
        yield "⚠️ Digite uma pergunta para começar."
        return

    if not _pronto.is_set():
        yield "⏳ Preparando a base de startups, só um instante..."
        _pronto.wait()
    if "erro" in _recursos:
        yield f"⚠️ Erro ao carregar a base de startups: {_recursos['erro']}"
        return

    try:
        mensagem_en = GoogleTranslator(source='auto', target='en').translate(mensagem)
    except Exception:
        mensagem_en = mensagem

    res = _recursos["collection"].query(query_texts=[mensagem_en], n_results=8)

    contexto = "\n".join(
        f"- {meta['name']} ({meta['batch']}, {meta['industry']}): {doc}"
        for doc, meta in zip(res["documents"][0], res["metadatas"][0])
    )

    prompt = f"""Você é um analista de oportunidades de negócio especializado em "tropicalização" de startups (adaptação de modelos internacionais ao Brasil).

O usuário quer saber sobre: "{mensagem}" (que em inglês significa: "{mensagem_en}")

Abaixo estão startups investidas pela Y Combinator que mais se aproximam do tema:

{contexto}

Responda OBRIGATORIAMENTE EM PORTUGUÊS seguindo esta estrutura:

**1. O que funciona lá fora**
(2-3 frases sintetizando os modelos listados)

**2. Gap no Brasil**
(o que aparentemente ainda não existe ou é mal atendido)

**3. Hipóteses a testar**
(2-3 perguntas concretas para validar antes de investir)

**4. Riscos e diferenças culturais/regulatórias**
(1-2 frases)

Seja direto, sem floreio. Não invente startups que não estão na lista. Se a lista não for suficiente, diga isso honestamente.
"""

    try:
        resposta = llm.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            stream=True,
        )
        texto_parcial = ""
        for chunk in resposta:
            delta = chunk.choices[0].delta.content
            if delta:
                texto_parcial += delta
                yield texto_parcial
    except Exception as e:
        yield f"⚠️ Erro ao consultar a IA: {e}"


def analisar_tema_da_url(request: gr.Request):
    """Quando o usuário vem da página inicial (/chat?q=...), já dispara a análise."""
    tema = (request.query_params.get("q") or "").strip()
    if not tema:
        yield gr.skip()
        return
    historico = [{"role": "user", "content": tema}]
    for parcial in responder_chat(tema, []):
        yield historico + [{"role": "assistant", "content": parcial}]


TEMA = gr.themes.Soft(
    primary_hue=gr.themes.colors.emerald,
    neutral_hue=gr.themes.colors.stone,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
).set(
    body_background_fill="#FBF7EF",
    button_primary_background_fill="#0E3B2C",
    button_primary_background_fill_hover="#17513D",
    button_primary_text_color="#FFFFFF",
    block_radius="16px",
)

CSS = """
.gradio-container { max-width: 900px !important; margin: auto; }
footer { display: none !important; }
.topo { display: flex; align-items: center; justify-content: space-between; padding: 8px 4px 4px; }
.topo a { text-decoration: none; }
.marca { display: flex; align-items: center; gap: 10px; font-family: "Fraunces", Georgia, serif;
         font-size: 1.35rem; font-weight: 700; color: #0E3B2C; }
.marca img { width: 34px; height: 34px; }
.voltar { color: #5B6B63; font-size: 0.92rem; }
.voltar:hover { color: #0E3B2C; }
.intro { text-align: center; margin: 6px 0 4px; }
.intro h2 { font-family: "Fraunces", Georgia, serif; font-size: 1.6rem; color: #0E3B2C; margin-bottom: 4px; }
.intro p { color: #5B6B63; font-size: 0.98rem; }
"""

HEAD = """
<link rel="icon" href="/static/logo.svg" type="image/svg+xml">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&display=swap" rel="stylesheet">
"""

with gr.Blocks(title="Tropicalize · Chat") as demo:
    gr.HTML("""
    <div class="topo">
        <a href="/" class="marca"><img src="/static/logo.svg" alt="">tropicalize</a>
        <a href="/" class="voltar">← Página inicial</a>
    </div>
    <div class="intro">
        <h2>O que funcionou lá fora e ainda não existe no Brasil?</h2>
        <p>Digite um tema de negócio e a IA busca startups parecidas na base da Y Combinator para analisar o gap brasileiro.</p>
    </div>
    """)
    chat = gr.ChatInterface(
        fn=responder_chat,
        chatbot=gr.Chatbot(show_label=False),
        examples=[
            "Ferramentas para gestão financeira de freelancers",
            "IA para revisão de documentos jurídicos",
            "Marketplace para serviços domésticos",
            "Software B2B para o mercado imobiliário",
            "Análise de assinaturas para SaaS",
        ],
        examples_label="💡 Exemplos de perguntas",
        textbox=gr.Textbox(
            placeholder="Digite um tema de negócio...",
            container=False,
            scale=7,
        ),
    )
    demo.load(analisar_tema_da_url, None, chat.chatbot).then(
        lambda historico: historico, chat.chatbot, chat.chatbot_state
    ).then(
        None, js="() => window.history.replaceState(null, '', window.location.pathname)"
    )

demo.queue()

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True, "base_pronta": "collection" in _recursos}


app = gr.mount_gradio_app(
    app, demo, path="/chat",
    theme=TEMA, css=CSS, head=HEAD,
    footer_links=[],
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
