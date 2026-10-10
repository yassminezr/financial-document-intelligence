
from pathlib import Path
import pymupdf

raw_dir = Path("data/raw")

for year in [2023, 2024, 2025]:
    pdf_path = raw_dir / f"microsoft_{year}.pdf"

    if not pdf_path.exists():
        print(f"Fichier introuvable : {pdf_path}")
        continue

    with pymupdf.open(pdf_path) as pdf:
        total_pages = len(pdf)
        total_characters = sum(
            len(page.get_text()) for page in pdf
        )

        print(f"\n--- Microsoft {year} ---")
        print(f"Nombre de pages : {total_pages}")
        print(f"Caractères extraits : {total_characters}")
        print("Première page :")
        print(pdf[0].get_text()[:300])
