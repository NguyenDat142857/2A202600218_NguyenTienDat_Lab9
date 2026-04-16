"""
workers/retrieval.py — Retrieval Worker (FINAL VERSION)
"""

import os

WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3


# ─────────────────────────────────────────────
# Embedding Function
# ─────────────────────────────────────────────

def _get_embedding_fn():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")

        def embed(text: str) -> list:
            return model.encode([text])[0].tolist()

        return embed
    except ImportError:
        pass

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        def embed(text: str) -> list:
            resp = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return resp.data[0].embedding

        return embed
    except ImportError:
        pass

    import random
    print("⚠️ Using random embeddings (fallback)")

    def embed(text: str) -> list:
        return [random.random() for _ in range(384)]

    return embed


# ─────────────────────────────────────────────
# ChromaDB Collection
# ─────────────────────────────────────────────

def _get_collection():
    import chromadb

    client = chromadb.PersistentClient(path="./chroma_db")

    try:
        return client.get_collection("day09_docs")
    except Exception:
        print("⚠️ Collection not found. Please run indexing step.")
        return client.get_or_create_collection("day09_docs")


# ─────────────────────────────────────────────
# Dense Retrieval
# ─────────────────────────────────────────────

def retrieve_dense(query: str, top_k: int = DEFAULT_TOP_K) -> list:
    embed = _get_embedding_fn()
    query_embedding = embed(query)

    try:
        collection = _get_collection()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        chunks = []

        for doc, dist, meta in zip(documents, distances, metadatas):
            source = meta.get("source", "unknown") if meta else "unknown"

            # Convert distance → similarity (safe fallback)
            score = round(max(0.0, 1 - float(dist)), 4) if dist is not None else 0.0

            chunks.append({
                "text": doc,
                "source": source,
                "score": score,
                "metadata": meta or {},
            })

        # Sort by score (cao → thấp)
        chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)

        return chunks

    except Exception as e:
        print(f"⚠️ Retrieval error: {e}")
        return []


# ─────────────────────────────────────────────
# Worker Entry
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    task = state.get("task", "")
    top_k = state.get("retrieval_top_k", DEFAULT_TOP_K)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("worker_io_logs", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": None,
        "error": None,
    }

    try:
        chunks = retrieve_dense(task, top_k=top_k)

        # Fallback nếu không có dữ liệu
        if not chunks:
            state["history"].append(f"[{WORKER_NAME}] no chunks found")
            chunks = [{
                "text": "No relevant documents found.",
                "source": "none",
                "score": 0.0,
                "metadata": {},
            }]

        sources = list({c["source"] for c in chunks})

        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources

        worker_io["output"] = {
            "chunks_count": len(chunks),
            "sources": sources,
        }

        state["history"].append(
            f"[{WORKER_NAME}] retrieved {len(chunks)} chunks from {sources}"
        )

    except Exception as e:
        worker_io["error"] = {
            "code": "RETRIEVAL_FAILED",
            "reason": str(e)
        }

        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []

        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state["worker_io_logs"].append(worker_io)

    return state


# ─────────────────────────────────────────────
# Standalone Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Retrieval Worker — Standalone Test")
    print("=" * 50)

    test_queries = [
        "SLA ticket P1 là bao lâu?",
        "Điều kiện được hoàn tiền là gì?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        result = run({"task": query})

        chunks = result.get("retrieved_chunks", [])

        print(f"  Retrieved: {len(chunks)} chunks")

        for c in chunks[:2]:
            print(f"    [{c['score']:.3f}] {c['source']}: {c['text'][:80]}...")

        print(f"  Sources: {result.get('retrieved_sources', [])}")

    print("\n✅ retrieval_worker test done.")