
from pathlib import Path

import pandas as pd

from src.extraction.financial_extractor import (
    extract_financial_data,
)
from src.extraction.normalization import (
    normalize_financial_data,
)


OUTPUT_PATH = Path(
    "data/processed/financial_metrics.csv"
)

YEARS = [2023, 2024, 2025]


def build_financial_dataset() -> pd.DataFrame:
    """
    Extract, normalize and consolidate financial
    metrics from the Microsoft annual reports.
    """
    records = []

    for year in YEARS:
        records.extend(
            extract_financial_data(year)
        )

    df = normalize_financial_data(records)

    # Check uniqueness of business keys
    business_keys = [
        "company",
        "fiscal_year",
        "metric",
    ]

    duplicates = df.duplicated(
        subset=business_keys,
        keep=False
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate financial metrics detected."
        )

    # Create output directory
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save structured dataset
    df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print("Financial dataset created successfully!")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Records: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


if __name__ == "__main__":
    dataset = build_financial_dataset()

    print("\n=== FINANCIAL DATASET ===")
    print(dataset.to_string(index=False))
