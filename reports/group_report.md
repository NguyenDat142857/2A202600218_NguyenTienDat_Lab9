# Báo Cáo Nhóm — Lab Day 08: Full RAG Pipeline

**Tên nhóm:** Cá nhân (Solo Project)  

**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Nguyễn Tiến Đạt | Full-stack (Retrieval + LLM + Eval + Docs) | ___ |

**Ngày nộp:** 14/04/2026  
**Repo:** ___  

---

## 1. Pipeline nhóm đã xây dựng

Pipeline được xây dựng theo kiến trúc RAG tiêu chuẩn gồm 3 bước: indexing → retrieval → generation.

**Chunking decision:**
Tôi sử dụng chunk_size khoảng 400–500 tokens, overlap ~50 tokens, và tách theo section của tài liệu. Lý do là các tài liệu có cấu trúc rõ ràng theo section, nên việc chunk theo section giúp giữ nguyên ngữ cảnh logic và tránh cắt câu giữa chừng.

**Embedding model:**
Sử dụng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` vì hỗ trợ tốt tiếng Việt và có tốc độ nhanh.

**Retrieval variant (Sprint 3):**
Tôi chọn **Dense + Rerank**. Dense retrieval giúp tìm nhanh candidate, còn rerank giúp cải thiện độ chính xác của top-k chunks trước khi đưa vào LLM.

---

## 2. Quyết định kỹ thuật quan trọng nhất

**Quyết định:** Chọn rerank thay vì hybrid retrieval

**Bối cảnh vấn đề:**
Dense retrieval đôi khi trả về các chunk không thực sự liên quan, dẫn đến LLM trả lời sai hoặc thiếu thông tin.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Hybrid (Dense + BM25) | Tốt cho keyword | Phức tạp, cần thêm index |
| Rerank (Cross-encoder) | Cải thiện precision | Tốn compute |
| Query expansion | Tăng recall | Khó kiểm soát |

**Phương án đã chọn và lý do:**
Tôi chọn rerank vì dễ implement và có thể cải thiện ngay chất lượng kết quả mà không cần thay đổi pipeline quá nhiều.

**Bằng chứng:**
Trong quá trình test, rerank giúp loại bỏ các chunk không liên quan và giữ lại các chunk có nội dung chính xác hơn, đặc biệt với các câu hỏi dạng policy hoặc quy trình.

---

## 3. Kết quả grading questions

**Ước tính điểm raw:** ~80 / 98  

**Câu tốt nhất:**  
SLA P1 — vì retrieval trả đúng chunk chứa thông tin rõ ràng, LLM dễ dàng trích xuất.

**Câu fail:**  
ERR-403-AUTH — do retrieval không tìm được context phù hợp.

**Câu gq07 (abstain):**  
Pipeline trả về đúng "Không đủ dữ liệu", chứng tỏ grounded prompt hoạt động đúng.

---

## 4. A/B Comparison — Baseline vs Variant

**Biến đã thay đổi:** bật rerank

| Metric | Baseline | Variant | Delta |
|--------|---------|---------|-------|
| Relevance | Medium | High | + |
| Accuracy | Medium | High | + |
| Hallucination | Medium | Low | - |

**Kết luận:**
Rerank giúp cải thiện đáng kể độ liên quan của context, từ đó tăng độ chính xác của câu trả lời. Tuy nhiên, nó không giải quyết được vấn đề thiếu recall trong retrieval.

---

## 5. Phân công và đánh giá nhóm

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Nguyễn Tiến Đạt | Toàn bộ pipeline | 2,3 |

**Điều làm tốt:**
Pipeline hoàn chỉnh end-to-end, có thể trả lời có citation và abstain đúng.

**Điều chưa tốt:**
Chưa implement hybrid retrieval nên một số query keyword bị fail.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì?

Tôi sẽ implement **hybrid retrieval** để cải thiện các query chứa keyword.

Ngoài ra, tôi sẽ xây dựng một hệ thống **evaluation tự động** để đo performance chính xác hơn thay vì đánh giá thủ công.

