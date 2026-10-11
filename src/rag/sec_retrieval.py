
import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


INDEX_DIR = Path("data/processed/rag/sec_index")

INDEX_PATH = INDEX_DIR / "faiss_full.index"
METADATA_PATH = INDEX_DIR / "chunks_full.jsonl"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SECFinancialRetriever:

    def __init__(self):
        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {INDEX_PATH}"
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                f"Chunk metadata not found: {METADATA_PATH}"
            )

        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(str(INDEX_PATH))

        with METADATA_PATH.open(
            "r", encoding="utf-8"
        ) as file:
            self.chunks = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        if self.index.ntotal != len(self.chunks):
            raise ValueError(
                "FAISS index and metadata count mismatch."
            )

        if self.index.d != 384:
            raise ValueError(
                "Unexpected embedding dimension."
            )

        print(
            f"Retriever loaded: "
            f"{self.index.ntotal} vectors"
        )

    def search(
        self,
        question: str,
        tickers: list[str] | None = None,
        fiscal_year: int | None = None,
        top_k: int = 5
    ) -> list[dict]:

        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        if tickers is not None:
            tickers = {
                ticker.upper() for ticker in tickers
            }

        query = self.model.encode(
            [question],
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        query = np.ascontiguousarray(
            query, dtype=np.float32
        )

        # Exact search across the index.
        # Metadata filters are applied afterwards.
        search_count = (
            self.index.ntotal
            if tickers is not None or fiscal_year is not None
            else min(top_k, self.index.ntotal)
        )

        scores, indices = self.index.search(
            query, search_count
        )

        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            chunk = self.chunks[int(idx)]

            if (
                tickers is not None
                and chunk["ticker"] not in tickers
            ):
                continue

            if (
                fiscal_year is not None
                and chunk["fiscal_year"] != fiscal_year
            ):
                continue

            results.append({
                "score": round(float(score), 4),
                "ticker": chunk["ticker"],
                "fiscal_year": chunk["fiscal_year"],
                "document": chunk["document"],
                "accession_number": chunk["accession_number"],
                "source_url": chunk["source_url"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"]
            })

            if len(results) >= top_k:
                break

        return results


def main():
    retriever = SECFinancialRetriever()

    tests = [
        {
            "question": "What drove Apple's revenue growth?",
            "tickers": ["AAPL"],
            "year": 2025
        },
        {
            "question": "What are NVIDIA's AI-related risks?",
            "tickers": ["NVDA"],
            "year": 2025
        },
        {
            "question": "What are the main cloud business risks?",
            "tickers": ["MSFT", "AMZN"],
            "year": 2024
        }
    ]

    for test in tests:
        print("\n" + "=" * 60)
        print("QUESTION:", test["question"])
        print("COMPANIES:", test["tickers"])
        print("YEAR:", test["year"])

        results = retriever.search(
            question=test["question"],
            tickers=test["tickers"],
            fiscal_year=test["year"],
            top_k=5
        )

        for rank, result in enumerate(results, 1):
            print(f"\nTOP {rank}")
            print("Score:", result["score"])
            print("Company:", result["ticker"])
            print("Year:", result["fiscal_year"])
            print("Document:", result["document"])
            print("Accession:", result["accession_number"])
            print("Text:", result["text"][:250], "...")


if __name__ == "__main__":
    main()
