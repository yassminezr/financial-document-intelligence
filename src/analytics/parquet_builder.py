
from pathlib import Path

import pandas as pd

from src.extraction.data_quality import (
    validate_financial_data,
)


INPUT_PATH = Path(
    "data/processed/financial_metrics.csv"
)

OUTPUT_PATH = Path(
    "data/processed/financial_metrics.parquet"
)


def build_parquet():
    """
    Validate financial data and export to Parquet.
    """

    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    # Read structured financial data
    df = pd.read_csv(INPUT_PATH)

    # Data Quality Gate
    report = validate_financial_data(df)

    if report["status"] != "PASSED":
        raise ValueError(
            f"Data Quality Gate FAILED: {report['checks']}"
        )

    # Convert numerical columns
    integer_columns = [
        "fiscal_year",
        "value_millions",
        "value_usd",
        "source_page",
    ]

    for column in integer_columns:
        df[column] = pd.to_numeric(
            df[column], errors="raise"
        ).astype("int64")

    # Generate Parquet
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_parquet(
        OUTPUT_PATH,
        engine="pyarrow",
        index=False
    )

    print("=== PARQUET EXPORT ===")
    print("Data Quality: PASSED")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Records: {len(df)}")
    print(
        f"File size: "
        f"{OUTPUT_PATH.stat().st_size:,} bytes"
    )


if __name__ == "__main__":
    build_parquet()
