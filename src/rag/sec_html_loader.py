
import argparse
import csv
import json
import re
import time
from pathlib import Path

from bs4 import BeautifulSoup


INVENTORY = Path(
    "data/processed/sec_filing_inventory.csv"
)

RAW_DIR = Path("data/raw/sec")

OUTPUT_DIR = Path("data/processed/rag/sec_text")


def extract_text(html_path):
    """
    Extract readable text from a SEC HTML filing.
    Remove scripts, styles and hidden XBRL content.
    """

    html = html_path.read_bytes()

    soup = BeautifulSoup(html, "lxml")

    for element in soup.find_all([
        "script", "style", "noscript",
        "ix:hidden", "ix:header"
    ]):
        element.decompose()

    for element in soup.find_all(
        attrs={"hidden": True}
    ):
        element.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    return re.sub(r"\s+", " ", text).strip()


def main(limit=None):
    with INVENTORY.open(
        newline="",
        encoding="utf-8"
    ) as file:
        records = list(csv.DictReader(file))

    if limit is not None:
        records = records[:limit]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    success = 0
    failed = 0
    total_characters = 0

    started = time.perf_counter()

    for index, record in enumerate(records, 1):
        ticker = record["ticker"]
        year = record["fiscal_year"]
        accession = record["accession_number"]

        html_path = (
            RAW_DIR / ticker / year /
            f"{accession}.html"
        )

        output_path = (
            OUTPUT_DIR /
            f"{ticker}_{year}.json"
        )

        print(
            f"[{index}/{len(records)}] "
            f"{ticker} {year}"
        )

        try:
            if not html_path.exists():
                raise FileNotFoundError(
                    str(html_path)
                )

            text = extract_text(html_path)

            if len(text) < 1000:
                raise ValueError(
                    "Extracted text is unexpectedly short."
                )

            document = {
                "ticker": ticker,
                "company": record["company"],
                "fiscal_year": int(year),
                "accession_number": accession,
                "source_url": record["filing_url"],
                "document": html_path.name,
                "text": text,
            }

            output_path.write_text(
                json.dumps(
                    document,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

            success += 1
            total_characters += len(text)

            print(
                f"  OK — {len(text):,} characters"
            )

        except Exception as error:
            failed += 1
            print(f"  FAILED — {error}")

    elapsed = time.perf_counter() - started

    print("\n=== SEC TEXT EXTRACTION REPORT ===")
    print(f"Documents attempted: {len(records)}")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Total characters: {total_characters:,}")
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")

    main(args.limit)
