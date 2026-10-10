
from pathlib import Path
import re

import pymupdf


FINANCIAL_PAGES = {
    2023: {"income": 54, "balance": 56},
    2024: {"income": 56, "balance": 58},
    2025: {"income": 49, "balance": 51},
}

METRICS = {
    "revenue": {
        "label": "Total revenue",
        "statement": "income"
    },
    "net_income": {
        "label": "Net income",
        "statement": "income"
    },
    "total_assets": {
        "label": "Total assets",
        "statement": "balance"
    }
}


def extract_metric(page, label):
    """
    Extract the first numeric value following
    an exact financial statement row label.
    """
    lines = page.get_text("text").splitlines()

    for index, line in enumerate(lines):
        if line.strip().lower() != label.lower():
            continue

        # Examine lines immediately after the label.
        nearby_text = " ".join(
            lines[index + 1:index + 7]
        )

        numbers = re.findall(
            r"(?<![\w])\(?-?\d{1,3}(?:,\d{3})+\)?(?![\w])",
            nearby_text
        )

        if numbers:
            value = numbers[0].replace(",", "")
            value = value.replace("(", "-").replace(")", "")

            return {
                "raw_value": numbers[0],
                "value": int(value)
            }

    raise ValueError(
        f"Could not extract metric: {label}"
    )


def extract_financial_data(year: int) -> list[dict]:
    pdf_path = Path(
        f"data/raw/microsoft_{year}.pdf"
    )

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    results = []

    with pymupdf.open(pdf_path) as pdf:
        for metric_name, config in METRICS.items():
            page_number = FINANCIAL_PAGES[year][
                config["statement"]
            ]

            page = pdf[page_number - 1]

            extracted = extract_metric(
                page,
                config["label"]
            )

            results.append({
                "company": "Microsoft Corporation",
                "fiscal_year": year,
                "metric": metric_name,
                "raw_value": extracted["raw_value"],
                "value": extracted["value"],
                "currency": "USD",
                "unit": "millions",
                "source_document": pdf_path.name,
                "source_page": page_number
            })

    return results


def main():
    for year in FINANCIAL_PAGES:
        print(f"\n--- MICROSOFT {year} ---")

        records = extract_financial_data(year)

        for record in records:
            print(
                f"{record['metric']}: "
                f"{record['value']:,} "
                f"({record['unit']} {record['currency']}) "
                f"— page {record['source_page']}"
            )


if __name__ == "__main__":
    main()
