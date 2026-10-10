
import pandas as pd

from src.extraction.financial_extractor import (
    extract_financial_data,
)


VALID_METRICS = {
    "revenue",
    "net_income",
    "total_assets",
}


def normalize_financial_data(
    records: list[dict],
) -> pd.DataFrame:
    """
    Normalize extracted financial metrics.
    """

    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError("No financial data to normalize.")

    required = [
        "company",
        "fiscal_year",
        "metric",
        "raw_value",
        "value",
        "currency",
        "unit",
        "source_document",
        "source_page",
    ]

    if df[required].isna().any().any():
        raise ValueError("Missing financial values.")

    if not df["metric"].isin(VALID_METRICS).all():
        raise ValueError("Unknown financial metric.")

    if not (df["currency"] == "USD").all():
        raise ValueError("Unexpected currency.")

    if not (df["unit"] == "millions").all():
        raise ValueError("Unexpected financial unit.")

    df["fiscal_year"] = df["fiscal_year"].astype(int)
    df["source_page"] = df["source_page"].astype(int)

    df["value_millions"] = pd.to_numeric(
        df["value"],
        errors="raise"
    ).astype("int64")

    df["value_usd"] = (
        df["value_millions"] * 1_000_000
    ).astype("int64")

    df = df.drop(columns=["value"])

    df = df[
        [
            "company",
            "fiscal_year",
            "metric",
            "raw_value",
            "value_millions",
            "value_usd",
            "currency",
            "unit",
            "source_document",
            "source_page",
        ]
    ]

    return df.sort_values(
        ["fiscal_year", "metric"]
    ).reset_index(drop=True)


def main():
    records = []

    for year in [2023, 2024, 2025]:
        records.extend(extract_financial_data(year))

    df = normalize_financial_data(records)

    print("\n=== NORMALIZED FINANCIAL DATA ===")
    print(df.to_string(index=False))

    print("\nData types:")
    print(df.dtypes)

    print(f"\nTotal records: {len(df)}")


if __name__ == "__main__":
    main()
