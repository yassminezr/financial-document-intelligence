
import argparse
import csv
import hashlib
import os
import time
from pathlib import Path

import boto3
import requests
from botocore.exceptions import ClientError


# ================================================
# CONFIGURATION
# ================================================

AWS_PROFILE = "financial-ai"
AWS_REGION = "eu-north-1"

BUCKET = "financial-document-intelligence-bucket"

INVENTORY_PATH = Path(
    "data/processed/sec_filing_inventory.csv"
)

LOCAL_DIR = Path("data/raw/sec")

REPORT_PATH = Path(
    "data/processed/sec_ingestion_report.csv"
)

MAX_FILE_BYTES = 50 * 1024 * 1024


# ================================================
# HELPERS
# ================================================

def calculate_sha256(path):
    sha = hashlib.sha256()

    with open(path, "rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            sha.update(block)

    return sha.hexdigest()


def download_document(url, path, user_agent):
    """
    Download a SEC filing with basic validation.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_path = path.with_suffix(".part")

    if temporary_path.exists():
        temporary_path.unlink()

    try:
        with requests.get(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate"
            },
            timeout=(15, 90),
            stream=True
        ) as response:

            response.raise_for_status()

            total_bytes = 0

            with open(temporary_path, "wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    total_bytes += len(chunk)

                    if total_bytes > MAX_FILE_BYTES:
                        raise ValueError(
                            "Document exceeds 50 MB."
                        )

                    file.write(chunk)

        # Validate the actual downloaded content.
        with open(temporary_path, "rb") as file:
            beginning = file.read(8192).lower()

        if not (
            b"<html" in beginning
            or b"<!doctype html" in beginning
            or b"<?xml" in beginning
        ):
            raise ValueError(
                "Downloaded file is not recognized "
                "as HTML or XML."
            )

        temporary_path.replace(path)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def s3_object_matches(s3, key, sha256):
    """
    Check whether the object already exists
    with the same SHA-256 metadata.
    """

    try:
        response = s3.head_object(
            Bucket=BUCKET,
            Key=key
        )

        return (
            response.get("Metadata", {}).get("sha256")
            == sha256
        )

    except ClientError as error:
        status = error.response.get(
            "ResponseMetadata", {}
        ).get("HTTPStatusCode")

        if status == 404:
            return False

        raise


# ================================================
# INGESTION
# ================================================

def ingest(limit):
    user_agent = os.environ.get("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is not configured."
        )

    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    s3 = session.client("s3")

    with INVENTORY_PATH.open(
        newline="",
        encoding="utf-8"
    ) as file:
        records = list(csv.DictReader(file))

    if limit is not None:
        records = records[:limit]

    results = []
    start_time = time.perf_counter()

    for position, record in enumerate(
        records,
        start=1
    ):
        ticker = record["ticker"]
        year = record["fiscal_year"]
        accession = record["accession_number"]

        filename = f"{accession}.html"

        local_path = (
            LOCAL_DIR / ticker / year / filename
        )

        s3_key = (
            f"raw/sec/{ticker}/{year}/{filename}"
        )

        status = "FAILED"
        error_message = ""
        file_size = 0
        sha256 = ""

        print(
            f"[{position}/{len(records)}] "
            f"{ticker} — {year}"
        )

        try:
            if not local_path.exists():
                download_document(
                    record["filing_url"],
                    local_path,
                    user_agent
                )

                # Keep requests comfortably below
                # SEC access-rate limits.
                time.sleep(0.5)

            file_size = local_path.stat().st_size
            sha256 = calculate_sha256(local_path)

            if s3_object_matches(
                s3,
                s3_key,
                sha256
            ):
                status = "SKIPPED"
                print("  Already stored in S3.")

            else:
                s3.upload_file(
                    str(local_path),
                    BUCKET,
                    s3_key,
                    ExtraArgs={
                        "ContentType": "text/html",
                        "Metadata": {
                            "sha256": sha256,
                            "ticker": ticker,
                            "fiscal_year": year,
                            "accession": accession
                        }
                    }
                )

                status = "UPLOADED"
                print("  Uploaded to S3.")

        except Exception as error:
            error_message = str(error)
            print(f"  ERROR: {error_message}")

        results.append({
            "ticker": ticker,
            "fiscal_year": year,
            "accession_number": accession,
            "status": status,
            "size_bytes": file_size,
            "sha256": sha256,
            "s3_key": s3_key,
            "error": error_message
        })

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with REPORT_PATH.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "ticker",
                "fiscal_year",
                "accession_number",
                "status",
                "size_bytes",
                "sha256",
                "s3_key",
                "error"
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    elapsed = time.perf_counter() - start_time

    uploaded = sum(
        r["status"] == "UPLOADED"
        for r in results
    )

    skipped = sum(
        r["status"] == "SKIPPED"
        for r in results
    )

    failed = sum(
        r["status"] == "FAILED"
        for r in results
    )

    successful_bytes = sum(
        r["size_bytes"]
        for r in results
        if r["status"] in ("UPLOADED", "SKIPPED")
    )

    print("\n=== SEC INGESTION REPORT ===")
    print(f"Documents processed: {len(results)}")
    print(f"Uploaded: {uploaded}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(
        f"Successful corpus size: "
        f"{successful_bytes / 1024 / 1024:.2f} MB"
    )
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of reports to process"
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")

    ingest(args.limit)
