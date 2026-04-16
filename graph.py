"""
graph.py — Supervisor Orchestrator (FINAL)

Flow:
Input → Supervisor → Retrieval → (Policy nếu cần) → Synthesis → Output
"""

import json
import os
from datetime import datetime
from typing import TypedDict, Literal, Optional

# ✅ Import REAL workers
from workers.retrieval import run as retrieval_run
from workers.policy_tool import run as policy_tool_run
from workers.synthesis import run as synthesis_run


# ─────────────────────────────────────────────
# 1. STATE
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    task: str

    route_reason: str
    risk_high: bool
    needs_tool: bool
    hitl_triggered: bool

    retrieved_chunks: list
    retrieved_sources: list
    policy_result: dict
    mcp_tools_used: list

    final_answer: str
    sources: list
    confidence: float

    history: list
    workers_called: list
    supervisor_route: str
    latency_ms: Optional[int]
    run_id: str


def make_initial_state(task: str) -> AgentState:
    return {
        "task": task,
        "route_reason": "",
        "risk_high": False,
        "needs_tool": False,
        "hitl_triggered": False,
        "retrieved_chunks": [],
        "retrieved_sources": [],
        "policy_result": {},
        "mcp_tools_used": [],
        "final_answer": "",
        "sources": [],
        "confidence": 0.0,
        "history": [],
        "workers_called": [],
        "supervisor_route": "",
        "latency_ms": None,
        "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    }


# ─────────────────────────────────────────────
# 2. SUPERVISOR
# ─────────────────────────────────────────────

def supervisor_node(state: AgentState) -> AgentState:
    task = state["task"].lower()

    route = "retrieval_worker"
    route_reason = "default retrieval"
    needs_tool = False
    risk_high = False

    policy_keywords = [
        "refund", "hoàn tiền", "flash sale", "policy",
        "cấp quyền", "access", "admin", "level"
    ]

    incident_keywords = [
        "p1", "sla", "ticket", "incident"
    ]

    risk_keywords = [
        "khẩn cấp", "emergency", "err-"
    ]

    if any(k in task for k in policy_keywords):
        route = "policy_tool_worker"
        route_reason = "policy query detected"
        needs_tool = True

    elif any(k in task for k in incident_keywords):
        route = "retrieval_worker"
        route_reason = "incident/SLA query detected"

    if any(k in task for k in risk_keywords):
        risk_high = True
        route_reason += " | risk_high"

    if "err-" in task:
        route = "human_review"
        route_reason = "unknown error → human review"

    state["supervisor_route"] = route
    state["route_reason"] = route_reason
    state["needs_tool"] = needs_tool
    state["risk_high"] = risk_high
    state["history"].append(f"[supervisor] {route_reason}")

    return state


def route_decision(state: AgentState) -> Literal["retrieval_worker", "policy_tool_worker", "human_review"]:
    return state.get("supervisor_route", "retrieval_worker")


# ─────────────────────────────────────────────
# 3. HUMAN REVIEW
# ─────────────────────────────────────────────

def human_review_node(state: AgentState) -> AgentState:
    state["hitl_triggered"] = True
    state["workers_called"].append("human_review")

    print("\n⚠️ HITL TRIGGERED → auto approve (lab mode)\n")

    # Sau approve → quay lại retrieval
    state["supervisor_route"] = "retrieval_worker"
    return state


# ─────────────────────────────────────────────
# 4. GRAPH EXECUTION
# ─────────────────────────────────────────────

def build_graph():
    def run(state: AgentState) -> AgentState:
        import time
        start = time.time()

        # 1. Supervisor
        state = supervisor_node(state)
        route = route_decision(state)

        # 2. Routing
        if route == "human_review":
            state = human_review_node(state)
            state = retrieval_run(state)

        elif route == "policy_tool_worker":
            # ⚠️ FIX QUAN TRỌNG: phải retrieval trước
            state = retrieval_run(state)
            state = policy_tool_run(state)

        else:
            state = retrieval_run(state)

        # 3. Synthesis (luôn chạy)
        state = synthesis_run(state)

        state["latency_ms"] = int((time.time() - start) * 1000)
        state["history"].append(f"[graph] done {state['latency_ms']}ms")

        return state

    return run


_graph = build_graph()


# ─────────────────────────────────────────────
# 5. API
# ─────────────────────────────────────────────

def run_graph(task: str) -> AgentState:
    state = make_initial_state(task)
    return _graph(state)


def save_trace(state: AgentState, output_dir: str = "./artifacts/traces") -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/{state['run_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return path


# ─────────────────────────────────────────────
# 6. TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Day 09 Graph — FINAL")
    print("=" * 60)

    queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng Flash Sale có được hoàn tiền không?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for q in queries:
        print(f"\n▶ {q}")
        result = run_graph(q)

        print("Route      :", result["supervisor_route"])
        print("Workers    :", result["workers_called"])
        print("Answer     :", result["final_answer"])
        print("Confidence :", result["confidence"])

        trace = save_trace(result)
        print("Trace      :", trace)

    print("\n✅ DONE")