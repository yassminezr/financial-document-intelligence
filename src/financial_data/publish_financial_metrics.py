
from pathlib import Path

import boto3
import pandas as pd


AWS_PROFILE = "financial-ai"
AWS_REGION = "eu-north-1"
BUCKET = "financial-document-intelligence-bucket"

INPUT_PATH = Path(
    "data/processed/financial_metrics_v2.csv"
)

OUTPUT_PATH = Path(
    "data/processed/financial_metrics_v2.parquet"
)

S3_KEY = (
    "processed/financial_metrics_v2/"
    "financial_metrics.parquet"
)


def main():
    df = pd.read_csv(
        INPUT_PATH,
        dtype={
            "ticker": "string",
            "metric": "string",
            "source_tag": "string",
            "accession_number": "string",
            "period_start": "string",
            "period_end": "string",
            "filed_date": "string",
        }
    )

    keys = ["ticker", "fiscal_year", "metric"]

    if df.empty:
        raise ValueError("Dataset is empty.")

    if df.duplicated(keys).any():
        raise ValueError("Duplicate financial metrics.")

    if df["value_usd"].isna().any():
        raise ValueError("Missing financial values.")

    df["fiscal_year"] = df["fiscal_year"].astype("int64")
    df["value_usd"] = df["value_usd"].astype("int64")

    df.to_parquet(
        OUTPUT_PATH,
        engine="pyarrow",
        index=False
    )

    # Verify local Parquet before uploading.
    verified = pd.read_parquet(OUTPUT_PATH)

    if len(verified) != len(df):
        raise ValueError("Parquet row count mismatch.")

    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    s3 = session.client("s3")

    s3.upload_file(
        str(OUTPUT_PATH),
        BUCKET,
        S3_KEY
    )

    print("\n=== FINANCIAL PARQUET REPORT ===")
    print(f"Companies: {df['ticker'].nunique()}")
    print(f"Rows: {len(df)}")
    print(f"Metrics: {df['metric'].nunique()}")
    print(f"Duplicate keys: {df.duplicated(keys).sum()}")
    print(f"Local file: {OUTPUT_PATH}")
    print(f"S3: s3://{BUCKET}/{S3_KEY}")


if __name__ == "__main__":
    main()
