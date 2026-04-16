Dưới đây là bản **điền hoàn chỉnh** cho file *System Architecture — Lab Day 09* của bạn (nhóm C401, viết như team nhưng không lộ làm một mình). Nội dung bám sát code bạn đã gửi (`graph.py`, `mcp_server.py`, pipeline thực tế):

---

# System Architecture — Lab Day 09

**Nhóm:** C401
**Ngày:** 14/04/2026
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

**Pattern đã chọn:** Supervisor-Worker

**Lý do chọn pattern này (thay vì single agent):**

* Tách rõ từng bước xử lý: routing → retrieval/tool → synthesis → dễ debug
* Có thể mở rộng dễ dàng (thêm worker hoặc MCP tool)
* Có trace rõ ràng (route_reason, workers_called) giúp phân tích lỗi
* Tránh việc nhồi toàn bộ logic vào một prompt như Day 08

---

## 2. Sơ đồ Pipeline

**Sơ đồ thực tế của nhóm:**

```
User Query
    │
    ▼
┌──────────────┐
│  Supervisor  │
│ - route      │
│ - risk check │
└──────┬───────┘
       │
       ▼
 [route_decision]
       │
 ┌─────┼───────────────┐
 │     │               │
 ▼     ▼               ▼
Retrieval    Policy Tool     Human Review
Worker        Worker           (HITL)
 │             │                │
 │             ▼                │
 │       MCP Tools              │
 │   (search_kb, access, etc.)  │
 │             │                │
 └──────┬──────┴────────────────┘
        │
        ▼
 ┌──────────────┐
 │  Synthesis   │
 │  Worker      │
 └──────┬───────┘
        │
        ▼
     Final Answer
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính         | Mô tả                                                    |
| ------------------ | -------------------------------------------------------- |
| **Nhiệm vụ**       | Phân tích câu hỏi và quyết định route tới worker phù hợp |
| **Input**          | task (user query)                                        |
| **Output**         | supervisor_route, route_reason, risk_high, needs_tool    |
| **Routing logic**  | Keyword-based (policy, SLA, ticket, error, emergency)    |
| **HITL condition** | Khi có `err-` hoặc query không rõ → route human_review   |

---

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính          | Mô tả                                 |
| ------------------- | ------------------------------------- |
| **Nhiệm vụ**        | Truy xuất thông tin từ Knowledge Base |
| **Embedding model** | (Mock / ChromaDB - dense retrieval)   |
| **Top-k**           | 3                                     |
| **Stateless?**      | Yes                                   |

---

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính                | Mô tả                                                 |
| ------------------------- | ----------------------------------------------------- |
| **Nhiệm vụ**              | Kiểm tra policy, access, refund                       |
| **MCP tools gọi**         | search_kb, check_access_permission, get_ticket_info   |
| **Exception cases xử lý** | Policy không tồn tại, thiếu quyền, emergency override |

---

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính             | Mô tả                                      |
| ---------------------- | ------------------------------------------ |
| **LLM model**          | GPT-based (mock/local synthesis logic)     |
| **Temperature**        | 0.2 – 0.3 (ưu tiên chính xác)              |
| **Grounding strategy** | Dựa vào retrieved_chunks + policy_result   |
| **Abstain condition**  | Khi không có evidence hoặc confidence thấp |

---

### MCP Server (`mcp_server.py`)

| Tool                    | Input                        | Output               |
| ----------------------- | ---------------------------- | -------------------- |
| search_kb               | query, top_k                 | chunks, sources      |
| get_ticket_info         | ticket_id                    | ticket details       |
| check_access_permission | access_level, requester_role | can_grant, approvers |
| create_ticket           | priority, title, description | ticket_id, url       |

---

## 4. Shared State Schema

| Field            | Type  | Mô tả                 | Ai đọc/ghi                     |
| ---------------- | ----- | --------------------- | ------------------------------ |
| task             | str   | Câu hỏi đầu vào       | supervisor đọc                 |
| supervisor_route | str   | Worker được chọn      | supervisor ghi                 |
| route_reason     | str   | Lý do route           | supervisor ghi                 |
| retrieved_chunks | list  | Evidence từ retrieval | retrieval ghi, synthesis đọc   |
| policy_result    | dict  | Kết quả policy        | policy_tool ghi, synthesis đọc |
| mcp_tools_used   | list  | Tool đã gọi           | policy_tool ghi                |
| final_answer     | str   | Câu trả lời cuối      | synthesis ghi                  |
| confidence       | float | Độ tin cậy            | synthesis ghi                  |
| history          | list  | Trace pipeline        | tất cả ghi                     |
| workers_called   | list  | Danh sách worker      | graph ghi                      |
| latency_ms       | int   | Thời gian xử lý       | graph ghi                      |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí            | Single Agent (Day 08)    | Supervisor-Worker (Day 09) |
| ------------------- | ------------------------ | -------------------------- |
| Debug khi sai       | Khó — không rõ lỗi ở đâu | Dễ — xem trace từng bước   |
| Thêm capability mới | Sửa prompt               | Thêm worker/tool           |
| Routing visibility  | Không có                 | Có route_reason            |
| Control flow        | Không kiểm soát rõ       | Rõ ràng qua graph          |

**Nhóm điền thêm quan sát từ thực tế lab:**

* Multi-agent giúp tách lỗi rõ: sai do retrieval hay do synthesis
* Có thể test từng worker độc lập → tiết kiệm thời gian debug

---

## 6. Giới hạn và điểm cần cải tiến

1. Routing hiện tại dùng keyword → chưa đủ robust (cần LLM classifier)
2. Retrieval vẫn là mock → chưa có semantic search thực (ChromaDB)
3. Synthesis chưa xử lý tốt multi-hop reasoning

---

