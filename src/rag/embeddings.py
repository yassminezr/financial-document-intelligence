
from pathlib import Path
import json

import numpy as np
from sentence_transformers import SentenceTransformer

from src.rag.pdf_loader import load_pdf_pages
from src.rag.chunking import chunk_pages


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

ARTIFACT_DIR = Path("data/processed/rag")

EMBEDDINGS_PATH = ARTIFACT_DIR / "embeddings.npy"
CHUNKS_PATH = ARTIFACT_DIR / "chunks.json"


def generate_embeddings():
    print("Loading PDF pages...")
    pages = load_pdf_pages()

    print("Generating chunks...")
    chunks = chunk_pages(pages)

    print(f"Total chunks: {len(chunks)}")

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    ).astype("float32")

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    np.save(EMBEDDINGS_PATH, embeddings)

    CHUNKS_PATH.write_text(
        json.dumps(
            chunks,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\n=== EMBEDDINGS REPORT ===")
    print(f"Chunks: {len(chunks)}")
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Vector dimension: {embeddings.shape[1]}")
    print(f"Saved embeddings: {EMBEDDINGS_PATH}")
    print(f"Saved metadata: {CHUNKS_PATH}")


if __name__ == "__main__":
    generate_embeddings()
