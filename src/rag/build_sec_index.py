
import argparse
import json
import re
import time
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


INPUT_DIR = Path("data/processed/rag/sec_text")
OUTPUT_DIR = Path("data/processed/rag/sec_index")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
BATCH_SIZE = 32


def split_text(text):
    """Split text into overlapping chunks."""
    text = re.sub(r"\s+", " ", text).strip()

    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))

        if end < len(text):
            boundary = text.rfind(
                " ", start + CHUNK_SIZE // 2, end
            )

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            yield chunk

        if end >= len(text):
            break

        start = max(start + 1, end - CHUNK_OVERLAP)


def build_index(limit=None):
    files = sorted(INPUT_DIR.glob("*.json"))

    if limit is not None:
        files = files[:limit]

    if not files:
        raise RuntimeError("No SEC text files found.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    suffix = "test" if limit is not None else "full"

    index_path = OUTPUT_DIR / f"faiss_{suffix}.index"
    metadata_path = OUTPUT_DIR / f"chunks_{suffix}.jsonl"

    model = SentenceTransformer(MODEL_NAME)
    index = faiss.IndexFlatIP(384)

    total_chunks = 0
    started = time.perf_counter()

    batch_texts = []
    batch_metadata = []

    def flush_batch(output):
        nonlocal total_chunks

        if not batch_texts:
            return

        vectors = model.encode(
            batch_texts,
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        vectors = np.ascontiguousarray(
            vectors, dtype=np.float32
        )

        index.add(vectors)

        for item in batch_metadata:
            output.write(
                json.dumps(item, ensure_ascii=False) + "\n"
            )

        total_chunks += len(batch_texts)

        batch_texts.clear()
        batch_metadata.clear()

    with metadata_path.open(
        "w", encoding="utf-8"
    ) as output:

        for position, path in enumerate(files, 1):
            document = json.loads(
                path.read_text(encoding="utf-8")
            )

            chunks_in_document = 0

            for chunk_number, text in enumerate(
                split_text(document["text"]), 1
            ):
                metadata = {
                    "chunk_id": (
                        f"{document['ticker']}_"
                        f"{document['fiscal_year']}_"
                        f"{chunk_number}"
                    ),
                    "ticker": document["ticker"],
                    "fiscal_year": document["fiscal_year"],
                    "accession_number": document[
                        "accession_number"
                    ],
                    "source_url": document["source_url"],
                    "document": document["document"],
                    "text": text,
                }

                batch_texts.append(text)
                batch_metadata.append(metadata)
                chunks_in_document += 1

                if len(batch_texts) >= BATCH_SIZE:
                    flush_batch(output)

            print(
                f"[{position}/{len(files)}] "
                f"{document['ticker']} "
                f"{document['fiscal_year']} — "
                f"{chunks_in_document} chunks",
                flush=True,
            )

        flush_batch(output)

    if index.ntotal != total_chunks:
        raise RuntimeError("FAISS index count mismatch.")

    faiss.write_index(index, str(index_path))

    elapsed = time.perf_counter() - started

    print("\n=== SEC FAISS INDEX REPORT ===")
    print(f"Documents: {len(files)}")
    print(f"Chunks indexed: {total_chunks}")
    print(f"Vector dimension: {index.d}")
    print(f"Index type: IndexFlatIP")
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(f"Index: {index_path}")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive.")

    build_index(args.limit)
