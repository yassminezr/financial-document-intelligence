
from pathlib import Path

from src.ingestion.metadata import generate_metadata
from src.ingestion.s3_client import S3Client


def main():
    raw_dir = Path("data/raw")
    s3 = S3Client()

    results = {
        "UPLOADED": 0,
        "UPDATED": 0,
        "SKIPPED": 0,
        "FAILED": 0
    }

    for pdf_path in sorted(raw_dir.glob("*.pdf")):
        try:
            metadata = generate_metadata(pdf_path)
            year = metadata["fiscal_year"]

            pdf_key = f"raw/reports/{pdf_path.name}"
            metadata_key = (
                f"processed/document_metadata/"
                f"microsoft_{year}.json"
            )

            existing = s3.get_metadata(metadata_key)
            pdf_exists = s3.object_exists(pdf_key)

            if (
                existing is not None
                and existing.get("sha256") == metadata["sha256"]
                and pdf_exists
            ):
                status = "SKIPPED"
                print(f"[SKIPPED] {pdf_path.name}")

            else:
                status = (
                    "UPDATED"
                    if existing is not None or pdf_exists
                    else "UPLOADED"
                )

                pdf_uri = s3.upload_pdf(
                    pdf_path,
                    pdf_key
                )

                metadata["s3_uri"] = pdf_uri
                metadata["status"] = status

                s3.upload_metadata(
                    metadata,
                    metadata_key
                )

                print(f"[{status}] {pdf_path.name}")

            results[status] += 1

        except Exception as error:
            results["FAILED"] += 1
            print(f"[FAILED] {pdf_path.name}: {error}")

    print("\n=== INGESTION SUMMARY ===")
    for status, count in results.items():
        print(f"{status}: {count}")


if __name__ == "__main__":
    main()
