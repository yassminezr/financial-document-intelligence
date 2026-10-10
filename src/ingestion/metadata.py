
from pathlib import Path
from datetime import datetime, timezone

import pymupdf

from src.ingestion.hashing import calculate_sha256


def generate_metadata(file_path: str | Path) -> dict:
    """
    Generate metadata for a Microsoft financial PDF.
    """
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    year = int(file_path.stem.split("_")[-1])
    sha256 = calculate_sha256(file_path)

    with pymupdf.open(file_path) as pdf:
        page_count = len(pdf)

    metadata = {
        "document_id": sha256,
        "filename": file_path.name,
        "company": "Microsoft Corporation",
        "fiscal_year": year,
        "file_size_bytes": file_path.stat().st_size,
        "page_count": page_count,
        "sha256": sha256,
        "ingestion_timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "source": (
            "https://www.microsoft.com/en-us/"
            "investor/annual-reports"
        )
    }

    return metadata
