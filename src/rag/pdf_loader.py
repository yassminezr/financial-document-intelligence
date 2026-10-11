
from pathlib import Path

import pymupdf


RAW_DIR = Path("data/raw")

YEARS = [2023, 2024, 2025]


def load_pdf_pages() -> list[dict]:
    """
    Extract text from financial reports
    while preserving page-level provenance.
    """
    pages = []

    for year in YEARS:
        pdf_path = RAW_DIR / f"microsoft_{year}.pdf"

        if not pdf_path.is_file():
            raise FileNotFoundError(pdf_path)

        with pymupdf.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf):
                text = page.get_text("text").strip()

                if not text:
                    continue

                pages.append({
                    "company": "Microsoft Corporation",
                    "fiscal_year": year,
                    "document": pdf_path.name,
                    "page": page_index + 1,
                    "text": text
                })

    return pages


def main():
    pages = load_pdf_pages()

    print("=== RAG DOCUMENT LOADING ===")
    print(f"Pages extracted: {len(pages)}")
    print(
        f"Total characters: "
        f"{sum(len(p['text']) for p in pages):,}"
    )

    print("\nFirst page:")
    print({
        key: value
        for key, value in pages[0].items()
        if key != "text"
    })

    print("\nText preview:")
    print(pages[0]["text"][:300])


if __name__ == "__main__":
    main()
