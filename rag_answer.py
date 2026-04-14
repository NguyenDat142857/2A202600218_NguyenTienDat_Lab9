import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

TOP_K_SEARCH = 10
TOP_K_SELECT = 3

# =========================
# CLEAN ANSWER (FIX CỨNG)
# =========================
def clean_answer(answer: str) -> str:
    # remove weird chars
    answer = re.sub(r"[【】†]", "", answer)

    # fix dạng [1†L1] → [1]
    answer = re.sub(r"\[(\d+)[^\]]*\]", r"[\1]", answer)

    # fix "text1" → "text [1]"
    answer = re.sub(r"(\D)(\d)(\s|$)", r"\1[\2]\3", answer)

    # remove invalid citations [4], [5]
    answer = re.sub(r"\[(?![1-3]\])\d+\]", "", answer)

    return answer.strip()


# =========================
# RETRIEVE DENSE
# =========================
def retrieve_dense(query: str, top_k: int = TOP_K_SEARCH):
    import chromadb
    from index import get_embedding, CHROMA_DB_DIR

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection("rag_lab")

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        output.append({
            "text": doc,
            "metadata": meta,
            "score": 1 - dist
        })

    return output


# =========================
# RERANK
# =========================
from sentence_transformers import CrossEncoder

RERANK_MODEL = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, candidates, top_k=TOP_K_SELECT):
    if not candidates:
        return []

    pairs = [[query, c["text"]] for c in candidates]
    scores = RERANK_MODEL.predict(pairs)

    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [c for c, _ in ranked[:top_k]]


# =========================
# BUILD CONTEXT
# =========================
def build_context_block(chunks):
    parts = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata", {})
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        score = c.get("score", 0)

        header = f"[{i}] {source}"
        if section:
            header += f" | {section}"
        if score:
            header += f" | score={score:.2f}"

        parts.append(f"{header}\n{c['text']}")

    return "\n\n".join(parts)


# =========================
# PROMPT
# =========================
def build_prompt(query, context):
    return f"""Answer ONLY from the context below.

Rules:
- Use ONLY information from the context
- If not enough information → say "Không đủ dữ liệu"
- Cite ONLY using [1], [2], [3]
- Citation MUST be exactly like [1]
- Do NOT output numbers like 1 or [4]
- Keep answer short
- Answer in Vietnamese

Question: {query}

Context:
{context}

Answer:"""


# =========================
# LLM CALL
# =========================
def call_llm(prompt):
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200,
    )

    return response.choices[0].message.content


# =========================
# MAIN RAG
# =========================
def rag_answer(query, use_rerank=True, verbose=False):
    # retrieve
    candidates = retrieve_dense(query)

    if verbose:
        print(f"\n[RAG] Query: {query}")
        print(f"[RAG] Retrieved {len(candidates)}")

    # rerank
    if use_rerank:
        candidates = rerank(query, candidates)
    else:
        candidates = candidates[:TOP_K_SELECT]

    # ❗ CHẶN HALLUCINATION
    if not candidates or len(" ".join([c["text"] for c in candidates])) < 50:
        return {
            "query": query,
            "answer": "Không đủ dữ liệu",
            "sources": []
        }

    # build prompt
    context = build_context_block(candidates)
    prompt = build_prompt(query, context)

    if verbose:
        print("\n[RAG] Prompt:\n", prompt[:500])

    # generate
    answer = call_llm(prompt)
    answer = clean_answer(answer)

    # ❗ fallback nếu model vẫn bịa
    if "[" not in answer:
        answer = "Không đủ dữ liệu"

    # sources unique
    sources = list(dict.fromkeys([
        c["metadata"].get("source", "unknown")
        for c in candidates
    ]))

    return {
        "query": query,
        "answer": answer,
        "sources": sources
    }


# =========================
# TEST
# =========================
if __name__ == "__main__":
    print("=" * 50)
    print("FINAL RAG TEST")
    print("=" * 50)

    queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng có thể hoàn tiền bao nhiêu ngày?",
        "Ai duyệt Level 3?",
        "ERR-403-AUTH là gì?"
    ]

    for q in queries:
        res = rag_answer(q, verbose=True)
        print("\nQ:", q)
        print("A:", res["answer"])
        print("Sources:", res["sources"])