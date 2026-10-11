
import json
import sys
import time
from pathlib import Path


# ============================================
# PROJECT IMPORTS
# ============================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.sec_retrieval import SECFinancialRetriever


QUESTIONS_PATH = (
    PROJECT_ROOT / "tests" /
    "rag_evaluation_questions.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" /
    "rag_evaluation_results.json"
)


# ============================================
# EVALUATION
# ============================================

def main():
    tests = json.loads(
        QUESTIONS_PATH.read_text(encoding="utf-8")
    )

    retriever = SECFinancialRetriever()

    results = []
    start = time.perf_counter()

    for i, test in enumerate(tests, 1):
        question = test["question"]
        tickers = test["tickers"]
        year = test["fiscal_year"]

        query_start = time.perf_counter()

        passages = retriever.search(
            question=question,
            tickers=tickers,
            fiscal_year=year,
            top_k=5
        )

        latency = time.perf_counter() - query_start

        filters_valid = all(
            passage["ticker"] in tickers
            and passage["fiscal_year"] == year
            for passage in passages
        )

        count_valid = len(passages) == 5

        passed = (
            filters_valid
            and count_valid
        )

        results.append({
            "question": question,
            "tickers": tickers,
            "fiscal_year": year,
            "retrieved_passages": len(passages),
            "filters_valid": filters_valid,
            "passed": passed,
            "latency_seconds": round(latency, 3),
            "top_score": (
                passages[0]["score"]
                if passages else None
            )
        })

        status = "PASS" if passed else "FAIL"

        print(
            f"[{i}/{len(tests)}] {status} "
            f"| {latency:.2f}s | {question}"
        )

    elapsed = time.perf_counter() - start

    passed_tests = sum(r["passed"] for r in results)

    average_latency = (
        sum(r["latency_seconds"] for r in results)
        / len(results)
        if results else 0
    )

    report = {
        "total_tests": len(results),
        "passed": passed_tests,
        "failed": len(results) - passed_tests,
        "average_retrieval_latency_seconds": round(
            average_latency, 3
        ),
        "total_elapsed_seconds": round(elapsed, 2),
        "results": results
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\n=== RAG EVALUATION REPORT ===")
    print(f"Questions: {len(results)}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(results) - passed_tests}")
    print(
        f"Average retrieval latency: "
        f"{average_latency:.3f} seconds"
    )
    print(f"Total elapsed: {elapsed:.2f} seconds")
    print(f"Report: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
