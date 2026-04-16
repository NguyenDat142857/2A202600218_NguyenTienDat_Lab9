"""
mcp_server.py — Mock MCP Server (FINAL)

Tools:
    1. search_kb
    2. get_ticket_info
    3. check_access_permission
    4. create_ticket
"""

import os
from datetime import datetime


# ─────────────────────────────────────────────
# TOOL SCHEMA (DISCOVERY)
# ─────────────────────────────────────────────

TOOL_SCHEMAS = {
    "search_kb": {
        "name": "search_kb",
        "description": "Semantic search KB",
    },
    "get_ticket_info": {
        "name": "get_ticket_info",
        "description": "Get ticket info (mock)",
    },
    "check_access_permission": {
        "name": "check_access_permission",
        "description": "Check access control rules",
    },
    "create_ticket": {
        "name": "create_ticket",
        "description": "Create ticket (mock)",
    },
}


# ─────────────────────────────────────────────
# TOOL 1 — SEARCH KB
# ─────────────────────────────────────────────

def tool_search_kb(query: str, top_k: int = 3) -> dict:
    try:
        from workers.retrieval import retrieve_dense

        chunks = retrieve_dense(query, top_k=top_k)

        return {
            "chunks": chunks,
            "sources": list({c.get("source", "unknown") for c in chunks}),
            "total_found": len(chunks),
        }

    except Exception as e:
        print(f"[MCP ERROR] search_kb failed: {e}")

        return {
            "chunks": [
                {
                    "text": f"[ERROR] KB search failed: {e}",
                    "source": "mcp_error",
                    "score": 0.0,
                }
            ],
            "sources": ["mcp_error"],
            "total_found": 0,
        }


# ─────────────────────────────────────────────
# TOOL 2 — TICKET INFO
# ─────────────────────────────────────────────

MOCK_TICKETS = {
    "P1-LATEST": {
        "ticket_id": "IT-9847",
        "priority": "P1",
        "status": "in_progress",
        "assignee": "oncall@company",
        "created_at": "2026-04-13T22:47:00",
        "sla_deadline": "2026-04-14T02:47:00",
    },
    "IT-1234": {
        "ticket_id": "IT-1234",
        "priority": "P2",
        "status": "open",
        "assignee": None,
        "created_at": "2026-04-13T09:15:00",
        "sla_deadline": "2026-04-14T09:15:00",
    },
}


def tool_get_ticket_info(ticket_id: str) -> dict:
    ticket = MOCK_TICKETS.get(ticket_id.upper())

    if ticket:
        return ticket

    return {
        "error": f"Ticket '{ticket_id}' not found",
        "available": list(MOCK_TICKETS.keys()),
    }


# ─────────────────────────────────────────────
# TOOL 3 — ACCESS CONTROL
# ─────────────────────────────────────────────

ACCESS_RULES = {
    1: ["Line Manager"],
    2: ["Line Manager", "IT Admin"],
    3: ["Line Manager", "IT Admin", "IT Security"],
}


def tool_check_access_permission(access_level: int, requester_role: str, is_emergency: bool = False) -> dict:
    if access_level not in ACCESS_RULES:
        return {"error": "Invalid access level (1-3 only)"}

    approvers = ACCESS_RULES[access_level]

    emergency_override = False
    notes = []

    if is_emergency:
        if access_level == 2:
            emergency_override = True
            notes.append("Emergency bypass allowed for Level 2")
        else:
            notes.append("No emergency bypass for this level")

    return {
        "can_grant": True,
        "required_approvers": approvers,
        "emergency_override": emergency_override,
        "notes": notes,
        "source": "access_control_sop.txt",
    }


# ─────────────────────────────────────────────
# TOOL 4 — CREATE TICKET
# ─────────────────────────────────────────────

def tool_create_ticket(priority: str, title: str, description: str = "") -> dict:
    ticket_id = f"IT-{1000 + abs(hash(title)) % 9000}"

    print(f"[MCP] Created ticket {ticket_id}")

    return {
        "ticket_id": ticket_id,
        "priority": priority,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "url": f"https://jira.local/{ticket_id}",
        "note": "MOCK ticket",
    }


# ─────────────────────────────────────────────
# REGISTRY
# ─────────────────────────────────────────────

TOOL_REGISTRY = {
    "search_kb": tool_search_kb,
    "get_ticket_info": tool_get_ticket_info,
    "check_access_permission": tool_check_access_permission,
    "create_ticket": tool_create_ticket,
}


def list_tools():
    return list(TOOL_SCHEMAS.values())


def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found"}

    try:
        return TOOL_REGISTRY[tool_name](**tool_input)
    except Exception as e:
        return {"error": f"Execution failed: {e}"}


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("MCP SERVER TEST")
    print("=" * 60)

    print("\nTools:")
    for t in list_tools():
        print("-", t["name"])

    print("\nTest search_kb:")
    res = dispatch_tool("search_kb", {"query": "SLA P1", "top_k": 2})
    for c in res.get("chunks", []):
        print(f"  [{c.get('score')}] {c.get('source')}")

    print("\nTest ticket:")
    print(dispatch_tool("get_ticket_info", {"ticket_id": "P1-LATEST"}))

    print("\nTest access:")
    print(dispatch_tool("check_access_permission", {
        "access_level": 3,
        "requester_role": "dev",
        "is_emergency": True
    }))

    print("\nTest create ticket:")
    print(dispatch_tool("create_ticket", {
        "priority": "P1",
        "title": "System down"
    }))

    print("\n✅ DONE")