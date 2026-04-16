import chromadb
import os
from sentence_transformers import SentenceTransformer

print("🚀 Starting index build...")

# Kết nối database
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("day09_docs")

# Load model embedding
model = SentenceTransformer("all-MiniLM-L6-v2")

# Đọc dữ liệu
docs_dir = "./data/docs"

ids = []
documents = []
metadatas = []

files = os.listdir(docs_dir)
print(f"📄 Found {len(files)} documents")

for i, fname in enumerate(files):
    print(f"👉 Processing: {fname}")

    with open(os.path.join(docs_dir, fname), encoding="utf-8") as f:
        content = f.read()

    ids.append(f"doc_{i}")
    documents.append(content)
    metadatas.append({"source": fname})

print("📦 Adding to ChromaDB...")

collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("✅ Index built successfully!")