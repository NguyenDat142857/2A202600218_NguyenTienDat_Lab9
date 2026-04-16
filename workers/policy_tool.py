"""
workers/policy_tool.py — Policy & Tool Worker
"""

import os
from datetime import datetime

WORKER_NAME = "policy_tool_worker"


# ─────────────────────────────────────────────
# MCP Client
# ─────────────────────────────────────────────

def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    try:
        from mcp_server import dispatch_tool

        result = dispatch_tool(tool_name, tool_input)

        return {
            "tool": tool_name,
            "input": tool_input,
            "output": result,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": None,
            "error": {"code": "MCP_CALL_FAILED", "reason": str(e)},
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# Policy Logic
# ─────────────────────────────────────────────

def analyze_policy(task: str, chunks: list) -> dict:
    task_lower = task.lower()
    context_text = " ".join([c.get("text", "") for c in chunks]).lower()

    exceptions_found = []

    # Flash Sale
    if "flash sale" in task_lower or "flash sale" in context_text:
        exceptions_found.append({
            "type": "flash_sale_exception",
            "rule": "Flash Sale orders are non-refundable.",
            "source": "policy_refund_v4.txt",
        })

    # Digital products
    if any(k in task_lower for k in ["license", "subscription", "digital"]):
        exceptions_found.append({
            "type": "digital_product_exception",
            "rule": "Digital products are non-refundable.",
            "source": "policy_refund_v4.txt",
        })

    # Activated
    if any(k in task_lower for k in ["đã kích hoạt", "activated", "used"]):
        exceptions_found.append({
            "type": "activated_exception",
            "rule": "Activated products cannot be refunded.",
            "source": "policy_refund_v4.txt",
        })

    policy_applies = len(exceptions_found) == 0

    sources = list({c.get("source", "unknown") for c in chunks})

    return {
        "policy_applies": policy_applies,
        "policy_name": "refund_policy_v4",
        "exceptions_found": exceptions_found,
        "source": sources,
        "explanation": "Rule-based policy analysis",
    }


# ─────────────────────────────────────────────
# Worker Entry
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "needs_tool": needs_tool,
        },
        "output": None,
        "error": None,
    }

    try:
        # 🔥 FIX: gọi MCP nếu chưa có chunks
        if not chunks and needs_tool:
            mcp_call = _call_mcp_tool("search_kb", {
                "query": task,
                "top_k": 3
            })

            state["mcp_tools_used"].append(mcp_call)
            state["history"].append("[policy_tool_worker] MCP search_kb called")

            if mcp_call["output"] and mcp_call["output"].get("chunks"):
                chunks = mcp_call["output"]["chunks"]
                state["retrieved_chunks"] = chunks
                state["retrieved_sources"] = [
                    c.get("source", "unknown") for c in chunks
                ]

        # 🔥 Policy analysis
        policy_result = analyze_policy(task, chunks)
        state["policy_result"] = policy_result

        # 🔥 Optional MCP call
        if needs_tool and any(k in task.lower() for k in ["ticket", "p1"]):
            mcp_call = _call_mcp_tool("get_ticket_info", {
                "ticket_id": "P1-LATEST"
            })
            state["mcp_tools_used"].append(mcp_call)
            state["history"].append("[policy_tool_worker] MCP get_ticket_info called")

        worker_io["output"] = {
            "policy_applies": policy_result["policy_applies"],
            "exceptions": len(policy_result["exceptions_found"]),
            "mcp_calls": len(state["mcp_tools_used"]),
        }

        state["history"].append(
            f"[policy_tool_worker] done | applies={policy_result['policy_applies']}"
        )

    except Exception as e:
        worker_io["error"] = {
            "code": "POLICY_FAILED",
            "reason": str(e)
        }
        state["history"].append(f"[policy_tool_worker] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)

    return state


# ─────────────────────────────────────────────
# Standalone Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Policy Tool Worker — Test")
    print("=" * 50)

    test_cases = [
        {
            "task": "Flash Sale refund có được không?",
            "retrieved_chunks": [{"text": "Flash Sale không được refund", "source": "policy_refund_v4.txt"}]
        },
        {
            "task": "Refund license key đã kích hoạt",
            "retrieved_chunks": [{"text": "Digital product không refund", "source": "policy_refund_v4.txt"}]
        }
    ]

    for tc in test_cases:
        result = run(tc.copy())
        print("\nTask:", tc["task"])
        print("Result:", result["policy_result"])