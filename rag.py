import os
import chromadb
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# ⚠️ COLE SUA CHAVE DO GROQ ENTRE AS ASPAS ABAIXO
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

llm = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

print("Carregando modelo de embeddings...")
model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("yc_startups")
print(f"Banco carregado: {collection.count()} startups\n")


def responder(pergunta_usuario: str) -> str:
    q_emb = model.encode(pergunta_usuario).tolist()
    res = collection.query(query_embeddings=[q_emb], n_results=8)

    contexto = ""
    for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
        contexto += f"- {meta['name']} ({meta['batch']}, {meta['industry']}): {doc}\n"

    prompt = f"""Você é um analista de oportunidades de negócio especializado em "tropicalização" de startups (adaptação de modelos internacionais ao Brasil).

O usuário quer saber: "{pergunta_usuario}"

Abaixo estão startups investidas pela Y Combinator que mais se aproximam do tema:

{contexto}

Responda seguindo esta estrutura:
1. **O que funciona lá fora** (2-3 frases sintetizando os modelos listados)
2. **Gap no Brasil** (o que aparentemente ainda não existe ou é mal atendido)
3. **Hipóteses a testar** (2-3 perguntas concretas para validar antes de investir)
4. **Riscos e diferenças culturais/regulatórias** (1-2 frases)

Seja direto, sem floreio. Não invente startups que não estão na lista. Se a lista não for suficiente, diga isso honestamente.
"""

    resposta = llm.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resposta.choices[0].message.content


print("Pergunte sobre qualquer tema (ou 'sair'):")
while True:
    pergunta = input("\n> ").strip()
    if pergunta.lower() in ("sair", "exit", "quit", ""):
        break
    print("\nAnalisando...\n")
    print(responder(pergunta))
    print("\n" + "=" * 60)

# Adicione esta verificação após a criação do cliente 'llm'
try:
    modelos_disponiveis = [m.id for m in llm.models.list()]
    print("Modelos disponíveis:", modelos_disponiveis)
    # Opcional: escolher um modelo da lista automaticamente
    # model_escolhido = "openai/gpt-oss-120b" if "openai/gpt-oss-120b" in modelos_disponiveis else modelos_disponiveis[0]
except Exception as e:
    print(f"Não foi possível listar os modelos: {e}")