
from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


ARTIFACT_DIR = Path("data/processed/rag")
INDEX_PATH = ARTIFACT_DIR / "faiss.index"
CHUNKS_PATH = ARTIFACT_DIR / "chunks.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class FinancialRetriever:

    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(str(INDEX_PATH))

        self.chunks = json.loads(
            CHUNKS_PATH.read_text(encoding="utf-8")
        )

        if self.index.ntotal != len(self.chunks):
            raise ValueError(
                "FAISS index and chunks mismatch."
            )

        if self.index.d != 384:
            raise ValueError(
                "Unexpected embedding dimension."
            )

    def search(
        self,
        question: str,
        top_k: int = 5,
        fiscal_year: int | None = None
    ) -> list[dict]:

        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_embedding = self.model.encode(
            [question],
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype("float32")

        query_embedding = np.ascontiguousarray(
            query_embedding
        )

        # Search the complete index before applying
        # metadata filtering, to avoid missing
        # relevant documents for a selected year.
        search_count = (
            self.index.ntotal
            if fiscal_year is not None
            else min(top_k, self.index.ntotal)
        )

        scores, indices = self.index.search(
            query_embedding,
            search_count
        )

        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            chunk = self.chunks[int(idx)]

            if (
                fiscal_year is not None
                and chunk["fiscal_year"] != fiscal_year
            ):
                continue

            results.append({
                "score": round(float(score), 4),
                "chunk_id": chunk["chunk_id"],
                "document": chunk["document"],
                "fiscal_year": chunk["fiscal_year"],
                "page": chunk["page"],
                "text": chunk["text"]
            })

            if len(results) >= top_k:
                break

        return results


def main():
    retriever = FinancialRetriever()

    tests = [
        {
            "question": (
                "What drove Microsoft's revenue "
                "growth in 2025?"
            ),
            "year": 2025
        },
        {
            "question": (
                "What are the main risks "
                "related to cloud services?"
            ),
            "year": None
        },
        {
            "question": (
                "How did Microsoft describe "
                "its AI investments in 2025?"
            ),
            "year": 2025
        }
    ]

    for test in tests:
        print(f"\n{'=' * 60}")
        print(f"QUESTION: {test['question']}")
        print(f"YEAR FILTER: {test['year']}")
        print(f"{'=' * 60}")

        results = retriever.search(
            question=test["question"],
            top_k=5,
            fiscal_year=test["year"]
        )

        for rank, result in enumerate(results, 1):
            print(f"\nTOP {rank}")
            print(f"Score: {result['score']}")
            print(f"Source: {result['document']}")
            print(f"Page: {result['page']}")
            print(f"Text: {result['text'][:300]}...")


if __name__ == "__main__":
    main()
