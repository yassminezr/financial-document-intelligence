
import hashlib

from src.ingestion.hashing import calculate_sha256


def test_hashing_is_deterministic(tmp_path):
    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"financial report")

    first_hash = calculate_sha256(file_path)
    second_hash = calculate_sha256(file_path)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_hash_changes_with_content(tmp_path):
    file_path = tmp_path / "sample.pdf"

    file_path.write_bytes(b"original")
    first_hash = calculate_sha256(file_path)

    file_path.write_bytes(b"modified")
    second_hash = calculate_sha256(file_path)

    assert first_hash != second_hash


def test_hash_matches_sha256_reference(tmp_path):
    file_path = tmp_path / "sample.pdf"
    content = b"microsoft financial report"
    file_path.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()

    assert calculate_sha256(file_path) == expected
