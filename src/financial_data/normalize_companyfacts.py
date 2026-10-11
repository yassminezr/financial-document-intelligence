
import json
from pathlib import Path

import pandas as pd


INPUT_DIR = Path("data/raw/companyfacts")
OUTPUT_PATH = Path(
    "data/processed/financial_metrics_v2.csv"
)

YEARS = range(2021, 2026)

# Ordered fallback tags; review comparability in DQ.
METRIC_TAGS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "net_income": ["NetIncomeLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "equity": ["StockholdersEquity"],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue"
    ],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities"
    ],
    "capital_expenditures": [
        "PaymentsToAcquirePropertyPlantAndEquipment"
    ],
}

COLUMNS = [
    "ticker", "fiscal_year", "metric",
    "value_usd", "source_tag", "accession_number",
    "period_start", "period_end", "filed_date",
]


def annual_candidate(observation, year, instant):
    if observation.get("form") != "10-K":
        return False

    if observation.get("end", "")[:4] != str(year):
        return False

    if instant:
        return "start" not in observation

    start = observation.get("start")
    end = observation.get("end")

    if not start or not end:
        return False

    duration = (
        pd.Timestamp(end) - pd.Timestamp(start)
    ).days

    return 330 <= duration <= 380


def extract_metric(facts, tags, year, instant):
    us_gaap = facts.get("us-gaap", {})

    for tag in tags:
        concept = us_gaap.get(tag)

        if not concept:
            continue

        observations = concept.get(
            "units", {}
        ).get("USD", [])

        candidates = [
            item for item in observations
            if annual_candidate(item, year, instant)
        ]

        if not candidates:
            continue

        # Prefer original annual filing, then later
        # submission date for deterministic selection.
        candidates.sort(
            key=lambda item: (
                item.get("fy") == year,
                item.get("fp") == "FY",
                item.get("filed", ""),
            ),
            reverse=True,
        )

        item = candidates[0]

        return {
            "value_usd": item["val"],
            "source_tag": tag,
            "accession_number": item.get("accn"),
            "period_start": item.get("start"),
            "period_end": item.get("end"),
            "filed_date": item.get("filed"),
        }

    return None


def main():
    rows = []

    files = sorted(INPUT_DIR.glob("*.json"))

    if not files:
        raise RuntimeError("No Company Facts JSON files found.")

    for path in files:
        ticker = path.stem
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        facts = data.get("facts", {})

        for year in YEARS:
            for metric, tags in METRIC_TAGS.items():
                instant = metric in {
                    "total_assets",
                    "total_liabilities",
                    "equity",
                    "cash",
                }

                result = extract_metric(
                    facts, tags, year, instant
                )

                if result is None:
                    continue

                rows.append({
                    "ticker": ticker,
                    "fiscal_year": year,
                    "metric": metric,
                    **result,
                })

    df = pd.DataFrame(rows, columns=COLUMNS)

    if df.empty:
        raise RuntimeError("No financial metrics extracted.")

    duplicates = df.duplicated(
        ["ticker", "fiscal_year", "metric"]
    ).sum()

    if duplicates:
        raise ValueError(
            f"Duplicate business keys: {duplicates}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True, exist_ok=True
    )

    df = df.sort_values(
        ["ticker", "fiscal_year", "metric"]
    )

    df.to_csv(OUTPUT_PATH, index=False)

    expected = len(files) * len(YEARS) * len(METRIC_TAGS)

    print("\n=== XBRL NORMALIZATION REPORT ===")
    print(f"Companies: {len(files)}")
    print(f"Expected metric slots: {expected}")
    print(f"Extracted metrics: {len(df)}")
    print(f"Coverage: {len(df) / expected * 100:.1f}%")
    print(f"Duplicate keys: {duplicates}")
    print(f"Saved: {OUTPUT_PATH}")

    print("\nCoverage by metric:")
    print(
        df.groupby("metric").size().to_string()
    )


if __name__ == "__main__":
    main()
