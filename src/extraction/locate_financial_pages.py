
from pathlib import Path
import re
import pymupdf

RAW_DIR = Path("data/raw")


def normalize(text):
    return re.sub(r"\s+", " ", text.upper()).strip()


def find_metric_pages(pdf_path):
    print(f"\n{'=' * 55}")
    print(f"REPORT: {pdf_path.name}")
    print(f"{'=' * 55}")

    with pymupdf.open(pdf_path) as pdf:
        for index, page in enumerate(pdf):
            text = page.get_text()
            lines = [
                normalize(line)
                for line in text.splitlines()
                if line.strip()
            ]

            has_revenue = any(
                re.match(r"^TOTAL REVENUE\b", line)
                for line in lines
            )

            has_net_income = any(
                re.match(r"^NET INCOME\b", line)
                for line in lines
            )

            has_total_assets = any(
                re.match(r"^TOTAL ASSETS\b", line)
                for line in lines
            )

            if has_revenue and has_net_income:
                print(
                    f"\nINCOME STATEMENT CANDIDATE: "
                    f"PDF page {index + 1}"
                )

                for line in lines:
                    if (
                        line.startswith("TOTAL REVENUE")
                        or line.startswith("NET INCOME")
                    ):
                        print(f"  {line}")

            if has_total_assets:
                print(
                    f"\nBALANCE SHEET CANDIDATE: "
                    f"PDF page {index + 1}"
                )

                for line in lines:
                    if line.startswith("TOTAL ASSETS"):
                        print(f"  {line}")


def main():
    for year in [2023, 2024, 2025]:
        pdf_path = RAW_DIR / f"microsoft_{year}.pdf"

        if pdf_path.exists():
            find_metric_pages(pdf_path)


if __name__ == "__main__":
    main()
