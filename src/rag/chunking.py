
import re

from src.rag.pdf_loader import load_pdf_pages


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving content."""
    return re.sub(r"\s+", " ", text).strip()


def chunk_pages(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[dict]:

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if not 0 <= overlap < chunk_size:
        raise ValueError(
            "overlap must be between 0 and chunk_size."
        )

    chunks = []
    step = chunk_size - overlap

    for page in pages:
        text = clean_text(page["text"])

        if not text:
            continue

        for start in range(0, len(text), step):
            end = min(start + chunk_size, len(text))
            content = text[start:end]

            if not content.strip():
                continue

            chunk_number = len(chunks)

            chunks.append({
                "chunk_id": (
                    f"{page['fiscal_year']}_"
                    f"p{page['page']}_"
                    f"c{chunk_number}"
                ),
                "company": page["company"],
                "fiscal_year": page["fiscal_year"],
                "document": page["document"],
                "page": page["page"],
                "text": content
            })

            if end == len(text):
                break

    return chunks


def main():
    pages = load_pdf_pages()
    chunks = chunk_pages(pages)

    print("=== RAG CHUNKING ===")
    print(f"Input pages: {len(pages)}")
    print(f"Generated chunks: {len(chunks)}")

    if chunks:
        print("\nFirst chunk metadata:")
        print({
            k: v for k, v in chunks[0].items()
            if k != "text"
        })

        print("\nFirst chunk preview:")
        print(chunks[0]["text"][:400])

        print(
            "\nAverage chunk length:",
            round(
                sum(len(c["text"]) for c in chunks)
                / len(chunks),
                2
            )
        )


if __name__ == "__main__":
    main()
