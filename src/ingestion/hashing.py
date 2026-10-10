
import hashlib
from pathlib import Path


def calculate_sha256(file_path: str | Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    The file is read in chunks to avoid loading
    the entire document into memory.
    """
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            sha256.update(chunk)

    return sha256.hexdigest()
