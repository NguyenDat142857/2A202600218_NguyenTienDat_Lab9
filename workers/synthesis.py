"""
workers/synthesis.py — Synthesis Worker
Sprint 2: Tổng hợp câu trả lời từ retrieved_chunks và policy_result.
"""

import os

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Bạn là trợ lý IT Helpdesk nội bộ.

Quy tắc:
1. CHỈ dùng thông tin từ context
2. Không đủ thông tin → nói rõ
3. Có citation [file]
4. Trả lời ngắn gọn, có cấu trúc
5. Nếu có exception → nói trước
"""


# ─────────────────────────────────────────────
# LLM CALL (optional)
# ─────────────────────────────────────────────

def _call_llm(messages: list) -> str:
    """Gọi LLM nếu có API key"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception:
        return None  # fallback xuống rule-based


# ─────────────────────────────────────────────
# BUILD CONTEXT
# ─────────────────────────────────────────────

def _build_context(chunks: list) -> str:
    if not chunks:
        return "(Không có context)"

    parts = []
    for c in chunks:
        parts.append(
            f"[{c.get('source','unknown')}] {c.get('text','')[:300]}"
        )
    return "\n".join(parts)


# ─────────────────────────────────────────────
# RULE-BASED SYNTHESIS (IMPORTANT)
# ─────────────────────────────────────────────

def _rule_based_answer(task: str, chunks: list, policy_result: dict) -> str:
    """
    Fallback nếu không có LLM → vẫn phải trả lời ĐÚNG + có citation
    """
    if not chunks:
        return "Không đủ thông tin trong tài liệu nội bộ."

    answer_parts = []

    # 1. Nếu có exception → nói trước
    exceptions = policy_result.get("exceptions_found", [])
    if exceptions:
        answer_parts.append("⚠️ Ngoại lệ áp dụng:")
        for ex in exceptions:
            answer_parts.append(f"- {ex['rule']} [{ex['source']}]")

    # 2. Extract info từ chunks (simple)
    main_chunk = chunks[0]
    text = main_chunk.get("text", "")
    source = main_chunk.get("source", "unknown")

    # heuristic simple
    if "sla" in task.lower():
        answer_parts.append(f"SLA được quy định như sau:")
        answer_parts.append(f"{text[:200]} [{source}]")

    elif "hoàn tiền" in task.lower() or "refund" in task.lower():
        if exceptions:
            answer_parts.append("→ Không thể hoàn tiền do vi phạm policy.")
        else:
            answer_parts.append("→ Có thể hoàn tiền nếu thỏa điều kiện:")
        answer_parts.append(f"{text[:200]} [{source}]")

    elif "cấp quyền" in task.lower() or "access" in task.lower():
        answer_parts.append("Quy trình cấp quyền:")
        answer_parts.append(f"{text[:200]} [{source}]")

    else:
        answer_parts.append(f"{text[:300]} [{source}]")

    return "\n".join(answer_parts)


# ─────────────────────────────────────────────
# CONFIDENCE
# ─────────────────────────────────────────────

def _estimate_confidence(chunks: list, answer: str, policy_result: dict) -> float:
    if not chunks:
        return 0.2

    avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)

    penalty = 0.05 * len(policy_result.get("exceptions_found", []))

    if "Không đủ thông tin" in answer:
        return 0.3

    return round(max(0.3, min(0.95, avg_score - penalty)), 2)


# ─────────────────────────────────────────────
# MAIN SYNTHESIS
# ─────────────────────────────────────────────

def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    context = _build_context(chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Câu hỏi: {task}\n\nContext:\n{context}"
        }
    ]

    # Try LLM
    answer = _call_llm(messages)

    # Fallback nếu không có LLM
    if not answer:
        answer = _rule_based_answer(task, chunks, policy_result)

    sources = list({c.get("source", "unknown") for c in chunks})
    confidence = _estimate_confidence(chunks, answer, policy_result)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }


# ─────────────────────────────────────────────
# WORKER ENTRY
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks": len(chunks),
        },
        "output": None,
        "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)

        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]

        worker_io["output"] = result

        state["history"].append(
            f"[{WORKER_NAME}] done | confidence={result['confidence']}"
        )

    except Exception as e:
        worker_io["error"] = str(e)
        state["final_answer"] = f"SYNTHESIS ERROR: {e}"
        state["confidence"] = 0.0

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Synthesis Worker Test")
    print("=" * 50)

    test_state = {
        "task": "SLA ticket P1 là bao lâu?",
        "retrieved_chunks": [
            {
                "text": "Phản hồi 15 phút, xử lý 4 giờ.",
                "source": "sla_p1_2026.txt",
                "score": 0.9,
            }
        ],
        "policy_result": {},
    }

    result = run(test_state)
    print("\nAnswer:\n", result["final_answer"])
    print("\nConfidence:", result["confidence"])