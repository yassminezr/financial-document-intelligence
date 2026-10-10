
from pathlib import Path
import json
from datetime import datetime, timezone

import pandas as pd


DATASET_PATH = Path(
    "data/processed/financial_metrics.csv"
)

REPORT_PATH = Path(
    "data/processed/data_quality_report.json"
)

EXPECTED_YEARS = {2023, 2024, 2025}

EXPECTED_METRICS = {
    "revenue",
    "net_income",
    "total_assets",
}

# Reference values from Microsoft financial statements
# Values expressed in millions USD.
EXPECTED_VALUES = {
    (2023, "revenue"): 211915,
    (2023, "net_income"): 72361,
    (2023, "total_assets"): 411976,
    (2024, "revenue"): 245122,
    (2024, "net_income"): 88136,
    (2024, "total_assets"): 512163,
    (2025, "revenue"): 281724,
    (2025, "net_income"): 101832,
    (2025, "total_assets"): 619003,
}


def validate_financial_data(df: pd.DataFrame) -> dict:
    checks = {}

    required_columns = [
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

    # 1. Completeness
    checks["completeness"] = (
        all(col in df.columns for col in required_columns)
        and not df[required_columns].isna().any().any()
        if all(col in df.columns for col in required_columns)
        else False
    )

    # Stop detailed checks if columns are missing
    if not checks["completeness"]:
        return {
            "status": "FAILED",
            "checks": checks
        }

    # 2. Uniqueness
    checks["uniqueness"] = not df.duplicated(
        subset=["company", "fiscal_year", "metric"]
    ).any()

    # 3. Validity
    years = set(df["fiscal_year"].astype(int))
    metrics = set(df["metric"])

    checks["validity"] = (
        years == EXPECTED_YEARS
        and metrics == EXPECTED_METRICS
        and (df["company"] == "Microsoft Corporation").all()
        and (df["currency"] == "USD").all()
        and (df["unit"] == "millions").all()
        and (df["value_millions"] > 0).all()
    )

    # 4. Traceability
    checks["traceability"] = all(
        Path(f"data/raw/{row.source_document}").is_file()
        and row.source_page > 0
        for row in df.itertuples()
    )

    # 5. Unit consistency
    checks["unit_consistency"] = (
        df["value_usd"]
        == df["value_millions"] * 1_000_000
    ).all()

    # 6. Reference values validation
    actual_values = {
        (int(row.fiscal_year), row.metric): int(
            row.value_millions
        )
        for row in df.itertuples()
    }

    checks["reference_values"] = (
        actual_values == EXPECTED_VALUES
    )

    status = (
        "PASSED"
        if all(checks.values())
        else "FAILED"
    )

    return {
        "status": status,
        "total_records": len(df),
        "checks": {
            key: bool(value)
            for key, value in checks.items()
        }
    }


def main():
    df = pd.read_csv(DATASET_PATH)

    report = validate_financial_data(df)

    report["validation_timestamp"] = (
        datetime.now(timezone.utc).isoformat()
    )

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORT_PATH.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print("\n=== DATA QUALITY REPORT ===")
    print(json.dumps(report, indent=2))

    if report["status"] != "PASSED":
        raise SystemExit("Data quality validation failed.")


if __name__ == "__main__":
    main()
