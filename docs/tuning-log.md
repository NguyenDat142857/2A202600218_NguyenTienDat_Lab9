Dưới đây là phiên bản **`tuning-log.md` chuẩn GitHub (đẹp, rõ ràng, có format tốt)** — bạn chỉ cần copy vào file là xong:

---

# 📊 Tuning Log — RAG Pipeline (Day 08 Lab)

> Ghi lại quá trình cải thiện pipeline theo phương pháp A/B testing
> Nguyên tắc: **chỉ thay đổi 1 biến mỗi lần**

---

## 🧪 Baseline (Sprint 2)

**📅 Ngày:** 14/04/2026

### ⚙️ Cấu hình

```python
retrieval_mode = "dense"
chunk_size = 300
overlap = 50
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = "gpt-4o-mini"
```

---

### 📈 Kết quả đánh giá

| Metric           | Score (/5) |
| ---------------- | ---------- |
| Faithfulness     | 4.0        |
| Answer Relevance | 4.0        |
| Context Recall   | 3.0        |
| Completeness     | 3.0        |

---

### ❗ Các câu hỏi yếu nhất

| Câu hỏi                  | Vấn đề                                    |
| ------------------------ | ----------------------------------------- |
| `ERR-403-AUTH là gì?`    | Không có context phù hợp → fail retrieval |
| `Approval Matrix là gì?` | Dense không match alias → recall thấp     |
| `Refund policy`          | Context bị cắt → thiếu thông tin          |

---

### 🧠 Phân tích lỗi (Error Tree)

* [ ] Indexing lỗi
* [x] Retrieval bỏ sót keyword / alias
* [x] Top-k chưa tối ưu
* [x] Prompt chưa đủ chặt
* [ ] Context quá dài

👉 **Root cause chính:** Retrieval chưa đủ chính xác (ranking chưa tốt)

---

## 🚀 Variant 1 — Dense + Rerank (Sprint 3)

**📅 Ngày:** 14/04/2026

### 🔁 Biến thay đổi

```diff
- use_rerank = False
+ use_rerank = True
```

---

### 🎯 Lý do chọn

Dense retrieval có thể tìm đúng tài liệu nhưng **không xếp hạng đúng mức độ liên quan**.

➡️ Rerank (cross-encoder) giúp:

* So sánh trực tiếp *query ↔ chunk*
* Chọn đúng chunk relevant nhất
* Giảm nhiễu trong top-k

---

### ⚙️ Cấu hình

```python
retrieval_mode = "dense"
chunk_size = 300
overlap = 50
top_k_search = 10
top_k_select = 3
use_rerank = True
llm_model = "gpt-4o-mini"
```

---

### 📊 So sánh kết quả

| Metric           | Baseline | Variant 1 | Δ Improvement |
| ---------------- | -------- | --------- | ------------- |
| Faithfulness     | 4.0      | 5.0       | +1.0          |
| Answer Relevance | 4.0      | 5.0       | +1.0          |
| Context Recall   | 3.0      | 4.0       | +1.0          |
| Completeness     | 3.0      | 4.0       | +1.0          |

---

### 🔍 Quan sát chi tiết

| Câu hỏi | Baseline | Variant 1 | Nhận xét                        |
| ------- | -------- | --------- | ------------------------------- |
| SLA P1  | ✅        | ✅         | Không đổi                       |
| Refund  | ⚠️       | ✅         | Cải thiện do chọn đúng chunk    |
| Level 3 | ⚠️       | ✅         | Rerank chọn đúng section        |
| ERR-403 | ❌        | ❌         | Không có data → không cải thiện |

---

### 📌 Kết luận

* ✅ Rerank **cải thiện rõ rệt chất lượng retrieval**
* ✅ Đặc biệt hiệu quả với:

  * Query mơ hồ
  * Query có nhiều candidate gần giống nhau
* ❌ Không giúp nếu **corpus không có thông tin**

👉 **Decision:** Giữ rerank trong pipeline final

---

## 📚 Lessons Learned

### 1. Lỗi phổ biến nhất

> Retrieval sai → toàn bộ pipeline sai theo
> (Dù LLM tốt vẫn không cứu được nếu context sai)

---

### 2. Biến ảnh hưởng lớn nhất

> 🔥 **Rerank (cross-encoder)**
> Tăng mạnh accuracy mà không cần đổi embedding

---

### 3. Insight quan trọng

* Dense retrieval = **recall tốt nhưng precision chưa cao**
* Rerank = **tăng precision**
* RAG tốt = **recall + precision + grounding**

---

## 🔮 Nếu có thêm thời gian

### 1. Hybrid Retrieval (BM25 + Dense)

* Giải quyết tốt:

  * Mã lỗi (`ERR-403`)
  * Keyword exact match
* Kỳ vọng tăng **Context Recall**

---

### 2. Query Transformation

* Expansion (alias, synonym)
* Ví dụ:

  * "Approval Matrix" → "Access Control SOP"

---

### 3. Improve Chunking

* Chunk theo section thay vì fixed size
* Tránh mất thông tin quan trọng

---

# ✅ Final Takeaway

> **"Garbage in → Garbage out" applies perfectly to RAG**

* Retrieval là phần quan trọng nhất
* Rerank là cách cải thiện nhanh và hiệu quả nhất
* Không có context → phải **abstain ("Không đủ dữ liệu")**

---


