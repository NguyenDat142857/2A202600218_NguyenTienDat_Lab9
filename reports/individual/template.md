Dưới đây là **bài hoàn chỉnh** cho file báo cáo cá nhân của bạn (viết ngôi “tôi”, có kỹ thuật, có bằng chứng, đúng format lab). Bạn chỉ cần copy vào:

`reports/individual/nguyen_tien_dat.md`

---

# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Tiến Đạt
**Vai trò trong nhóm:** Supervisor Owner & Trace & Docs Owner
**Ngày nộp:** 14/04/2026

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

**Module/file tôi chịu trách nhiệm:**

* File chính: `graph.py`
* Functions tôi implement: `supervisor_node()`, `route_decision()`, `build_graph()`, `human_review_node()`

Trong lab này, tôi chịu trách nhiệm thiết kế và implement phần **Supervisor Orchestrator**, đóng vai trò điều phối toàn bộ pipeline multi-agent. Cụ thể, tôi xây dựng logic routing dựa trên keyword để quyết định chuyển task sang `retrieval_worker`, `policy_tool_worker` hoặc `human_review`.

Ngoài ra, tôi cũng thiết kế flow execution trong `build_graph()` để đảm bảo pipeline luôn kết thúc bằng `synthesis_worker` và có thể trace đầy đủ qua `history`, `workers_called`, `route_reason`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Supervisor là entry point của hệ thống, nên toàn bộ worker (retrieval, policy, synthesis) đều phụ thuộc vào routing của tôi. Nếu routing sai, toàn bộ pipeline sẽ cho kết quả sai dù worker đúng.

**Bằng chứng:**

* File: `graph.py`
* Function có comment rõ: `# --- Improved routing logic ---`
* Trace output trong `artifacts/traces/*.json` có field `route_reason`, `supervisor_route`

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Sử dụng keyword-based routing trong `supervisor_node` thay vì dùng LLM classifier

**Lý do:**

Trong quá trình thiết kế supervisor, tôi cân nhắc giữa:

1. Dùng LLM để classify intent (chính xác cao hơn)
2. Dùng keyword matching (nhanh, đơn giản)

Tôi quyết định chọn **keyword-based routing** vì:

* Latency rất thấp (không cần gọi LLM)
* Dễ debug (có thể thấy rõ vì sao match keyword)
* Đủ chính xác cho domain nhỏ (SLA, ticket, policy, access)

Ví dụ:

* `"refund", "hoàn tiền"` → policy_tool_worker
* `"p1", "sla", "ticket"` → retrieval_worker
* `"err-"` → human_review

**Trade-off đã chấp nhận:**

* Không xử lý tốt các câu paraphrase phức tạp
* Có thể mis-route nếu câu hỏi không chứa keyword rõ ràng

**Bằng chứng từ trace/code:**

```python
if any(k in task for k in policy_keywords):
    route = "policy_tool_worker"
    route_reason = "Detected policy/refund/access related query"

elif any(k in task for k in incident_keywords):
    route = "retrieval_worker"
    route_reason = "Detected incident/SLA/ticket query"
```

Trace:

```json
{
  "supervisor_route": "retrieval_worker",
  "route_reason": "Detected incident/SLA/ticket query",
  "latency_ms": 45
}
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Policy worker không có context retrieval → synthesis thiếu thông tin

**Symptom:**

Khi chạy query liên quan đến policy (ví dụ: hoàn tiền), pipeline chỉ gọi `policy_tool_worker` mà không gọi `retrieval_worker`. Kết quả:

* `retrieved_chunks` = []
* `final_answer` rất chung chung hoặc thiếu evidence

**Root cause:**

Trong `build_graph()`, khi route = `policy_tool_worker`, tôi không đảm bảo retrieval được gọi trước hoặc sau policy.

```python
elif route == "policy_tool_worker":
    state = policy_tool_worker_node(state)
```

→ Thiếu retrieval context

**Cách sửa:**

Tôi thêm logic:

```python
if not state["retrieved_chunks"]:
    state = retrieval_worker_node(state)
```

→ đảm bảo luôn có evidence trước khi synthesis

**Bằng chứng trước/sau:**

Trước khi sửa:

```json
"retrieved_chunks": [],
"final_answer": "[PLACEHOLDER] ... từ 0 chunks"
```

Sau khi sửa:

```json
"retrieved_chunks": [
  {"text": "SLA P1: phản hồi 15 phút...", "score": 0.92}
],
"final_answer": "[PLACEHOLDER] ... từ 1 chunks"
```

→ Answer có grounding tốt hơn

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Tôi thiết kế được một supervisor rõ ràng, có trace đầy đủ (`route_reason`, `workers_called`) giúp debug dễ dàng. Pipeline chạy ổn định và có thể mở rộng.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Routing hiện tại vẫn đơn giản (keyword-based), chưa xử lý được các câu hỏi phức tạp hoặc ambiguous. Ngoài ra, chưa tối ưu confidence scoring.

**Nhóm phụ thuộc vào tôi ở đâu?**

Toàn bộ flow phụ thuộc vào supervisor. Nếu routing sai hoặc thiếu logic, tất cả worker phía sau sẽ hoạt động sai.

**Phần tôi phụ thuộc vào thành viên khác:**

Tôi phụ thuộc vào:

* Retrieval worker để có dữ liệu đúng
* Synthesis worker để tạo câu trả lời cuối

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ thay thế keyword routing bằng **LLM-based intent classification** (hybrid approach).

Lý do: Trong một số trace, các câu không chứa keyword rõ ràng bị route sai. Ví dụ câu hỏi dạng paraphrase không match `"sla"` hoặc `"refund"`.

Tôi sẽ:

* Dùng LLM classify → fallback sang keyword nếu confidence thấp
* Log thêm `routing_confidence` trong trace

→ Giúp tăng routing accuracy và giảm lỗi silent failure

---


