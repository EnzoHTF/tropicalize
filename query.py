import chromadb
from sentence_transformers import SentenceTransformer

# Carrega o MESMO modelo usado na construção (obrigatório!)
print("Carregando modelo...")
model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("yc_startups")

print(f"Banco carregado: {collection.count()} startups\n")

while True:
    pergunta = input("Digite sua pergunta (ou 'sair' para encerrar): ").strip()
    if pergunta.lower() in ("sair", "exit", "quit", ""):
        break
    
    q_emb = model.encode(pergunta).tolist()
    res = collection.query(query_embeddings=[q_emb], n_results=5)
    
    print(f"\n--- Top 5 startups relacionadas a: '{pergunta}' ---")
    for i, (doc, meta, dist) in enumerate(zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ), 1):
        print(f"{i}. {meta['name']} ({meta['batch']}, {meta['industry']})")
        print(f"   {doc}")
        print(f"   [distância: {dist:.3f}]\n")
    print("=" * 60 + "\n")