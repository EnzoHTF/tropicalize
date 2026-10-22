import json
import chromadb
from sentence_transformers import SentenceTransformer

# 1. Carrega os dados
with open("all.json", "r", encoding="utf-8") as f:
    startups = json.load(f)

print(f"Startups carregadas: {len(startups)}")
print("Campos disponíveis:", list(startups[0].keys()))

# 2. Carrega o modelo de embeddings
print("Carregando modelo (primeira vez baixa ~80MB)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Prepara documentos, ids e metadados
docs, ids, metas = [], [], []
for i, s in enumerate(startups):
    desc = (s.get("one_liner") or s.get("long_description") or "").strip()
    if not desc:
        continue
    docs.append(desc)
    ids.append(f"startup_{i}")
    metas.append({
        "name": s.get("name", ""),
        "batch": s.get("batch", ""),
        "industry": s.get("industry", ""),
    })

print(f"Startups com descrição válida: {len(docs)}")

# 4. Cria o banco Chroma
client = chromadb.PersistentClient(path="./chroma_db")

# Apaga se existir (para evitar duplicar ao rodar 2x)
try:
    client.delete_collection("yc_startups")
except Exception:
    pass

collection = client.create_collection("yc_startups")

# 5. Gera os embeddings em lote
print("Gerando embeddings... (pode levar vários minutos, não feche o terminal)")
embeddings = model.encode(docs, batch_size=64, show_progress_bar=True)

# 6. Adiciona ao banco em lotes menores para não exceder o limite do ChromaDB
BATCH_SIZE = 4000
total_docs = len(docs)
print(f"Inserindo {total_docs} documentos no ChromaDB em lotes de {BATCH_SIZE}...")

for i in range(0, total_docs, BATCH_SIZE):
    end = min(i + BATCH_SIZE, total_docs)
    print(f"  -> Inserindo lote de {i} a {end-1}...")
    collection.add(
        documents=docs[i:end],
        embeddings=embeddings[i:end].tolist(),
        ids=ids[i:end],
        metadatas=metas[i:end],
    )

print(f"✅ Banco criado com {collection.count()} startups em ./chroma_db")

# 7. Teste de busca
print("\n--- Teste de busca ---")
pergunta = "tools for managing freelance finances"
q_emb = model.encode(pergunta).tolist()
res = collection.query(query_embeddings=[q_emb], n_results=5)

for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
    print(f"[{dist:.3f}] {meta['name']} ({meta['batch']}, {meta['industry']}) — {doc}")