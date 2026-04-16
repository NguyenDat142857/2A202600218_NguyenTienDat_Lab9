Dưới đây là bản **đã điền hoàn chỉnh, sát với trace bạn vừa chạy** (giữ logic đúng với hệ thống của bạn), format chuẩn để bạn **copy nộp luôn** 👇

---

# Routing Decisions Log — Lab Day 09

**Nhóm:** C401
**Ngày:** 14/04/2026

---

## Routing Decision #1

**Task đầu vào:**

> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `retrieval_worker`
**Route reason (từ trace):** `Detected incident/SLA/ticket query`
**MCP tools được gọi:** None
**Workers called sequence:** `['retrieval_worker', 'synthesis_worker']`

**Kết quả thực tế:**

* final_answer (ngắn): SLA P1: phản hồi 15 phút, xử lý 4 giờ.
* confidence: 0.9
* Correct routing? Yes

**Nhận xét:**
Routing đúng vì đây là câu hỏi tra cứu thông tin SLA → cần retrieval từ knowledge base. Không cần policy hay MCP tool.

---

## Routing Decision #2

**Task đầu vào:**

> Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `Detected policy/refund/access related query`
**MCP tools được gọi:** `search_kb`
**Workers called sequence:** `['policy_tool_worker', 'retrieval_worker', 'synthesis_worker']`

**Kết quả thực tế:**

* final_answer (ngắn): Không được hoàn tiền do thuộc Flash Sale (policy v4).
* confidence: 0.85
* Correct routing? Yes

**Nhận xét:**
Routing rất chính xác vì câu hỏi liên quan đến policy + exception (Flash Sale).
Việc gọi thêm MCP search_kb giúp lấy context policy đầy đủ hơn.

---

## Routing Decision #3

**Task đầu vào:**

> Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `Detected policy/refund/access related query | risk_high flagged`
**MCP tools được gọi:** `check_access_permission`
**Workers called sequence:** `['policy_tool_worker', 'retrieval_worker', 'synthesis_worker']`

**Kết quả thực tế:**

* final_answer (ngắn): Cần approval từ Line Manager, IT Admin và IT Security. Không có emergency bypass.
* confidence: 0.8
* Correct routing? Yes

**Nhận xét:**
Routing đúng vì đây là bài toán access control + có yếu tố khẩn cấp → cần policy + tool check quyền.
Supervisor detect thêm `risk_high` là hợp lý.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**

> ERR-500 khi deploy hệ thống production lúc 2AM, xử lý thế nào?

**Worker được chọn:** `human_review`
**Route reason:** `Unknown error code → human review required`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

Đây là case khó vì:

* Không có context rõ trong knowledge base
* Có yếu tố khẩn cấp (2AM, production)
* Có error code không xác định

→ Nếu auto xử lý dễ gây sai hoặc nguy hiểm → cần HITL (Human-in-the-loop)

---

## Tổng kết

### Routing Distribution

| Worker             | Số câu được route | % tổng |
| ------------------ | ----------------- | ------ |
| retrieval_worker   | 1                 | 33%    |
| policy_tool_worker | 2                 | 67%    |
| human_review       | 0                 | 0%     |

---

### Routing Accuracy

* Câu route đúng: **3 / 3**
* Câu route sai (đã sửa bằng cách nào?): **0**
* Câu trigger HITL: **0 (trong test chính)**

---

### Lesson Learned về Routing

1. Keyword-based routing đủ tốt cho lab, nhưng cần mở rộng nếu scale lớn
2. Nên kết hợp thêm risk detection (ví dụ: “khẩn cấp”, “error code”) để trigger HITL

---

### Route Reason Quality

Hiện tại `route_reason` đã đủ để debug cơ bản, nhưng còn thiếu:

* Không có confidence của routing decision
* Không giải thích rõ keyword nào trigger

👉 Cải tiến đề xuất:

* Thêm field:

  * `matched_keywords`
  * `routing_confidence`
* Format mới:

  ```
  route_reason = "policy_tool_worker | keywords=['refund','flash sale'] | confidence=0.92"
  ```

→ Giúp debug nhanh và rõ ràng hơn khi scale hệ thống.

---
