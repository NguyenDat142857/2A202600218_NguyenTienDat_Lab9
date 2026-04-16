"""
eval_trace.py — Trace Evaluation & Comparison
Sprint 4: Chạy pipeline với test questions, phân tích trace, so sánh single vs multi.
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import Optional

# Import graph
sys.path.insert(0, os.path.dirname(__file__))
from graph import run_graph, save_trace


# ─────────────────────────────────────────────
# 1. Run Pipeline on Test Questions
# ─────────────────────────────────────────────

def run_test_questions(questions_file: str = "data/test_questions.json") -> list:
    if not os.path.exists(questions_file):
        print(f"❌ File {questions_file} không tồn tại!")
        return []

    with open(questions_file, encoding="utf-8") as f:
        questions = json.load(f)

    print(f"\n📋 Running {len(questions)} test questions")
    print("=" * 60)

    results = []

    for i, q in enumerate(questions, 1):
        q_id = q.get("id", f"q{i:02d}")
        question_text = q.get("question", "")

        print(f"[{i:02d}] {q_id}: {question_text[:60]}...")

        try:
            result = run_graph(question_text)
            result["question_id"] = q_id

            # Save trace
            trace_file = save_trace(result)

            print(f"  ✓ route={result.get('supervisor_route')} | "
                  f"conf={result.get('confidence', 0):.2f} | "
                  f"{result.get('latency_ms', 0)}ms")

            results.append({
                "id": q_id,
                "question": question_text,
                "result": result,
            })

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({
                "id": q_id,
                "question": question_text,
                "error": str(e),
            })

    print("\n✅ Test run complete")
    return results


# ─────────────────────────────────────────────
# 2. Run Grading Questions
# ─────────────────────────────────────────────

def run_grading_questions(questions_file: str = "data/grading_questions.json") -> str:
    if not os.path.exists(questions_file):
        print("❌ grading_questions.json chưa có (đợi sau 17:00)")
        return ""

    with open(questions_file, encoding="utf-8") as f:
        questions = json.load(f)

    os.makedirs("artifacts", exist_ok=True)
    output_file = "artifacts/grading_run.jsonl"

    print(f"\n🎯 Running {len(questions)} grading questions")
    print("=" * 60)

    with open(output_file, "w", encoding="utf-8") as out:
        for i, q in enumerate(questions, 1):
            q_id = q.get("id", f"gq{i:02d}")
            question_text = q.get("question", "")

            print(f"[{i:02d}] {q_id}")

            try:
                result = run_graph(question_text)

                record = {
                    "id": q_id,
                    "question": question_text,
                    "answer": result.get("final_answer"),
                    "sources": result.get("sources", []),
                    "route": result.get("supervisor_route"),
                    "confidence": result.get("confidence"),
                    "latency_ms": result.get("latency_ms"),
                    "timestamp": datetime.now().isoformat(),
                }

                print(f"  ✓ {record['route']} | {record['confidence']:.2f}")

            except Exception as e:
                record = {
                    "id": q_id,
                    "question": question_text,
                    "answer": f"ERROR: {e}",
                    "confidence": 0,
                }
                print(f"  ✗ ERROR: {e}")

            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n✅ Saved → {output_file}")
    return output_file


# ─────────────────────────────────────────────
# 3. Analyze Traces
# ─────────────────────────────────────────────

def analyze_traces(traces_dir: str = "artifacts/traces") -> dict:
    if not os.path.exists(traces_dir):
        print("⚠️ Chưa có traces")
        return {}

    files = [f for f in os.listdir(traces_dir) if f.endswith(".json")]

    if not files:
        print("⚠️ Folder traces trống")
        return {}

    traces = []
    for f in files:
        with open(os.path.join(traces_dir, f), encoding="utf-8") as fp:
            traces.append(json.load(fp))

    routing = {}
    confidences = []
    latencies = []
    mcp_count = 0

    for t in traces:
        route = t.get("supervisor_route", "unknown")
        routing[route] = routing.get(route, 0) + 1

        if t.get("confidence"):
            confidences.append(t["confidence"])

        if t.get("latency_ms"):
            latencies.append(t["latency_ms"])

        if t.get("mcp_tools_used"):
            mcp_count += 1

    total = len(traces)

    metrics = {
        "total": total,
        "routing": routing,
        "avg_confidence": round(sum(confidences)/len(confidences), 2) if confidences else 0,
        "avg_latency_ms": int(sum(latencies)/len(latencies)) if latencies else 0,
        "mcp_usage_rate": f"{mcp_count}/{total}",
    }

    return metrics


# ─────────────────────────────────────────────
# 4. Compare Single vs Multi
# ─────────────────────────────────────────────

def compare_single_vs_multi():
    multi = analyze_traces()

    baseline = {
        "avg_confidence": 0.6,
        "avg_latency_ms": 200,
        "note": "Dummy baseline (update from Day08)"
    }

    return {
        "time": datetime.now().isoformat(),
        "day08": baseline,
        "day09": multi,
        "insight": [
            "Multi-agent dễ debug hơn",
            "Có routing rõ ràng",
            "Extend được bằng MCP tools",
        ]
    }


# ─────────────────────────────────────────────
# 5. Save Report
# ─────────────────────────────────────────────

def save_eval_report(data: dict) -> str:
    os.makedirs("artifacts", exist_ok=True)
    path = "artifacts/eval_report.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--grading", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    if args.grading:
        run_grading_questions()

    elif args.analyze:
        metrics = analyze_traces()
        print("\n📊 Metrics:")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))

    elif args.compare:
        report = compare_single_vs_multi()
        path = save_eval_report(report)
        print(f"\n📄 Saved → {path}")

    else:
        run_test_questions()
        metrics = analyze_traces()
        print("\n📊 Metrics:")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))

        report = compare_single_vs_multi()
        path = save_eval_report(report)
        print(f"\n📄 Eval report → {path}")