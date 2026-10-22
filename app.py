import os
# Otimização para o Render (evita que a IA trave o processador fraquinho)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb
import gradio as gr
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator

# ✅ Lê a chave da variável de ambiente
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

llm = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Carrega o modelo e o banco
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("yc_startups")

CSS = """
.gradio-container { max-width: 900px !important; margin: auto; }
.header {
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    margin-bottom: 1rem;
    color: white;
}
.header h1 { color: white; font-size: 2.5rem; margin-bottom: 0.5rem; }
.examples {
    margin-top: 15px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
}
.examples::before {
    content: "💡 Exemplos de perguntas:";
    width: 100%;
    text-align: center;
    font-weight: bold;
    color: #555;
    margin-bottom: 5px;
    font-size: 0.9rem;
}
.examples button {
    background-color: #f3f4f6 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 20px !important;
    padding: 8px 16px !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}
.examples button:hover {
    background-color: #dbeafe !important;
    border-color: #3b82f6 !important;
    color: #1e40af !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}
"""

def responder_chat(mensagem, historico):
    if not mensagem or not mensagem.strip():
        yield "⚠️ Digite uma pergunta para começar."
        return

    try:
        mensagem_en = GoogleTranslator(source='auto', target='en').translate(mensagem)
    except Exception:
        mensagem_en = mensagem

    q_emb = model.encode(mensagem_en).tolist()
    res = collection.query(query_embeddings=[q_emb], n_results=8)

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

demo = gr.ChatInterface(
    fn=responder_chat,
    title="🌎 Tropicalize",
    description="""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="font-size: 1.6rem; font-weight: 700; color: #4b5563; margin-bottom: 10px;">
            O que funcionou lá fora e ainda não existe no Brasil?
        </h2>
        <p style="font-size: 1rem; color: #6b7280;">
            Digite qualquer tema de negócio e a IA vai buscar startups parecidas na base da Y Combinator para analisar o gap brasileiro.
        </p>
    </div>
    """,
    examples=[
        "Ferramentas para gestão financeira de freelancers",
        "IA para revisão de documentos jurídicos",
        "Marketplace para serviços domésticos",
        "Software B2B para o mercado imobiliário",
        "Análise de assinaturas para SaaS",
    ],
    textbox=gr.Textbox(
        placeholder="Digite sua pergunta aqui...", 
        container=False, 
        scale=7
    ),
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)