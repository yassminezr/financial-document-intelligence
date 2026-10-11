
from pathlib import Path
import json

import faiss
import numpy as np


ARTIFACT_DIR = Path("data/processed/rag")

EMBEDDINGS_PATH = ARTIFACT_DIR / "embeddings.npy"
CHUNKS_PATH = ARTIFACT_DIR / "chunks.json"
INDEX_PATH = ARTIFACT_DIR / "faiss.index"


def build_faiss_index():
    """
    Build a FAISS index from normalized embeddings.
    """

    embeddings = np.load(
        EMBEDDINGS_PATH,
        allow_pickle=False
    )

    chunks = json.loads(
        CHUNKS_PATH.read_text(encoding="utf-8")
    )

    if embeddings.ndim != 2:
        raise ValueError("Embeddings must be a 2D matrix.")

    if len(embeddings) != len(chunks):
        raise ValueError(
            "Mismatch between embeddings and chunks."
        )

    if len(chunks) == 0:
        raise ValueError("No chunks available.")

    # FAISS requires float32 vectors
    embeddings = np.ascontiguousarray(
        embeddings,
        dtype=np.float32
    )

    dimension = embeddings.shape[1]

    # Exact similarity search using inner product
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(
        index,
        str(INDEX_PATH)
    )

    print("\n=== FAISS INDEX REPORT ===")
    print(f"Vectors indexed: {index.ntotal}")
    print(f"Vector dimension: {index.d}")
    print(f"Index type: IndexFlatIP")
    print(f"Saved index: {INDEX_PATH}")


if __name__ == "__main__":
    build_faiss_index()
