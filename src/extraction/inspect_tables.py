
from pathlib import Path
import pymupdf

PAGES = {
    2023: {"income": 54, "balance": 56},
    2024: {"income": 56, "balance": 58},
    2025: {"income": 49, "balance": 51},
}

KEYWORDS = [
    "TOTAL REVENUE",
    "NET INCOME",
    "TOTAL ASSETS",
]


def inspect_page(pdf, page_number):
    page = pdf[page_number - 1]
    lines = page.get_text("text").splitlines()

    for index, line in enumerate(lines):
        if any(
            keyword in line.upper()
            for keyword in KEYWORDS
        ):
            print(f"\n  Found: {line.strip()}")

            start = max(0, index - 3)
            end = min(len(lines), index + 10)

            for i in range(start, end):
                print(
                    f"    {i:03d}: {lines[i]}"
                )


def main():
    for year, pages in PAGES.items():
        pdf_path = Path(
            f"data/raw/microsoft_{year}.pdf"
        )

        with pymupdf.open(pdf_path) as pdf:
            print(f"\n{'=' * 55}")
            print(f"MICROSOFT {year}")
            print(f"{'=' * 55}")

            for statement, page_number in pages.items():
                print(
                    f"\n{statement.upper()} "
                    f"— PDF PAGE {page_number}"
                )

                inspect_page(pdf, page_number)


if __name__ == "__main__":
    main()
