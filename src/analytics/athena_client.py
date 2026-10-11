
import time
from pathlib import Path

import boto3
import pandas as pd


AWS_PROFILE = "financial-ai"
AWS_REGION = "eu-north-1"
DATABASE = "financial_intelligence"
WORKGROUP = "primary"

OUTPUT_LOCATION = (
    "s3://financial-document-intelligence-bucket/"
    "artifacts/athena-results/"
)


def run_athena_query(sql: str) -> pd.DataFrame:
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    athena = session.client("athena")

    response = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={
            "Database": DATABASE,
            "Catalog": "AwsDataCatalog"
        },
        ResultConfiguration={
            "OutputLocation": OUTPUT_LOCATION
        },
        WorkGroup=WORKGROUP
    )

    query_id = response["QueryExecutionId"]
    print(f"Query ID: {query_id}")

    # Wait for execution to finish
    deadline = time.monotonic() + 90

    while time.monotonic() < deadline:
        execution = athena.get_query_execution(
            QueryExecutionId=query_id
        )

        status_info = execution[
            "QueryExecution"
        ]["Status"]

        status = status_info["State"]

        if status == "SUCCEEDED":
            break

        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(
                f"Athena {status}: "
                f"{status_info.get('StateChangeReason', '')}"
            )

        time.sleep(1)

    else:
        athena.stop_query_execution(
            QueryExecutionId=query_id
        )
        raise TimeoutError("Athena query timed out.")

    # Retrieve all result pages
    paginator = athena.get_paginator(
        "get_query_results"
    )

    rows = []

    for page in paginator.paginate(
        QueryExecutionId=query_id
    ):
        rows.extend(
            page["ResultSet"]["Rows"]
        )

    if not rows:
        return pd.DataFrame()

    def parse_row(row):
        return [
            cell.get("VarCharValue")
            for cell in row["Data"]
        ]

    columns = parse_row(rows[0])
    values = [
        parse_row(row)
        for row in rows[1:]
    ]

    return pd.DataFrame(
        values,
        columns=columns
    )


def main():
    sql_path = Path(
        "sql/financial_analytics.sql"
    )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    df = run_athena_query(sql)

    # Convert result columns to numeric types
    for column in df.columns:
        if column != "fiscal_year":
            df[column] = pd.to_numeric(
                df[column],
                errors="raise"
            )

    df["fiscal_year"] = pd.to_numeric(
        df["fiscal_year"],
        errors="raise"
    ).astype("int64")

    print("\n=== ATHENA FINANCIAL ANALYTICS ===")
    print(df.to_string(index=False))
    print(f"\nRecords: {len(df)}")


if __name__ == "__main__":
    main()
