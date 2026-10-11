
import argparse
import csv
import json
import os
import time
from pathlib import Path

import boto3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ================================================
# CONFIGURATION
# ================================================

AWS_PROFILE = "financial-ai"
AWS_REGION = "eu-north-1"

BUCKET = "financial-document-intelligence-bucket"

INVENTORY = Path(
    "data/processed/sec_filing_inventory.csv"
)

OUTPUT_DIR = Path(
    "data/raw/companyfacts"
)


# ================================================
# HTTP SESSION WITH RETRY
# ================================================

def create_http_session():

    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=2,
        status_forcelist=[
            429, 500, 502, 503, 504
        ],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy
    )

    session.mount("https://", adapter)

    return session


# ================================================
# JSON VALIDATION
# ================================================

def validate_companyfacts(data, expected_cik):

    if int(data["cik"]) != int(expected_cik):
        raise ValueError(
            "Unexpected CIK in Company Facts."
        )

    if not isinstance(data.get("facts"), dict):
        raise ValueError(
            "Invalid Company Facts structure."
        )

    if not data["facts"]:
        raise ValueError(
            "No financial facts found."
        )


# ================================================
# MAIN INGESTION
# ================================================

def main(limit=None):

    user_agent = os.getenv("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is required."
        )

    with INVENTORY.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    # One request per company, not per document.
    companies = {}

    for row in rows:
        companies[row["ticker"]] = row["cik"]

    companies = sorted(companies.items())

    if limit is not None:
        companies = companies[:limit]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    aws_session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    s3 = aws_session.client("s3")
    http = create_http_session()

    success = 0
    skipped = 0
    failed = 0

    start_time = time.perf_counter()

    for ticker, cik in companies:

        print(f"Fetching {ticker}...")

        local_path = (
            OUTPUT_DIR / f"{ticker}.json"
        )

        s3_key = (
            f"raw/companyfacts/{ticker}.json"
        )

        try:

            # ------------------------------------
            # Resume previously completed downloads
            # ------------------------------------

            if local_path.exists():

                try:
                    existing_data = json.loads(
                        local_path.read_text(
                            encoding="utf-8"
                        )
                    )

                    validate_companyfacts(
                        existing_data,
                        cik
                    )

                    print(
                        "  SKIPPED — valid local "
                        "file already exists."
                    )

                    skipped += 1
                    continue

                except (
                    ValueError,
                    KeyError,
                    TypeError
                ):
                    print(
                        "  Invalid local file. "
                        "Downloading again."
                    )

            # ------------------------------------
            # Download Company Facts
            # ------------------------------------

            url = (
                "https://data.sec.gov/api/xbrl/"
                f"companyfacts/CIK{int(cik):010d}.json"
            )

            response = http.get(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept-Encoding": "gzip, deflate"
                },
                timeout=(15, 60)
            )

            response.raise_for_status()

            data = response.json()

            validate_companyfacts(
                data,
                cik
            )

            # ------------------------------------
            # Save locally
            # ------------------------------------

            temporary_path = local_path.with_suffix(
                ".json.part"
            )

            temporary_path.write_text(
                json.dumps(data),
                encoding="utf-8"
            )

            temporary_path.replace(
                local_path
            )

            # ------------------------------------
            # Upload to Amazon S3
            # ------------------------------------

            s3.upload_file(
                str(local_path),
                BUCKET,
                s3_key,
                ExtraArgs={
                    "ContentType": "application/json"
                }
            )

            success += 1

            size_kb = (
                local_path.stat().st_size / 1024
            )

            print(
                f"  UPLOADED — {size_kb:.1f} KB"
            )

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
            OSError,
            Exception
        ) as error:

            failed += 1

            print(
                f"  FAILED — {error}"
            )

        # Respect the SEC request-rate limits.
        time.sleep(0.5)

    elapsed = time.perf_counter() - start_time

    print("\n=== COMPANY FACTS REPORT ===")
    print(f"Companies attempted: {len(companies)}")
    print(f"Uploaded: {success}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Elapsed: {elapsed:.2f} seconds")

    print(
        f"Local JSON files: "
        f"{len(list(OUTPUT_DIR.glob('*.json')))}"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error(
            "--limit must be positive."
        )

    main(args.limit)
