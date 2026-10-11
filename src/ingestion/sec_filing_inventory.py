
import csv
import os
import time
from pathlib import Path

import requests


# First validation: two companies.
# Expand to 20 only after this test succeeds.

COMPANIES = {
    "MSFT": {"name": "Microsoft", "cik": 789019},
    "AAPL": {"name": "Apple", "cik": 320193},
    "GOOGL": {"name": "Alphabet", "cik": 1652044},
    "AMZN": {"name": "Amazon", "cik": 1018724},
    "META": {"name": "Meta", "cik": 1326801},
    "NVDA": {"name": "NVIDIA", "cik": 1045810},
    "TSLA": {"name": "Tesla", "cik": 1318605},
    "INTC": {"name": "Intel", "cik": 50863},
    "AMD": {"name": "AMD", "cik": 2488},
    "ORCL": {"name": "Oracle", "cik": 1341439},
    "CRM": {"name": "Salesforce", "cik": 1108524},
    "ADBE": {"name": "Adobe", "cik": 796343},
    "CSCO": {"name": "Cisco", "cik": 858877},
    "NFLX": {"name": "Netflix", "cik": 1065280},
    "PYPL": {"name": "PayPal", "cik": 1633917},
    "IBM": {"name": "IBM", "cik": 51143},
    "QCOM": {"name": "Qualcomm", "cik": 804328},
    "TXN": {"name": "Texas Instruments", "cik": 97476},
    "AVGO": {"name": "Broadcom", "cik": 1730168},
    "WMT": {"name": "Walmart", "cik": 104169}
}


TARGET_YEARS = set(range(2021, 2026))

OUTPUT_PATH = Path(
    "data/processed/sec_filing_inventory.csv"
)



def get_filings(ticker, company):
    user_agent = os.environ.get("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            "Set the SEC_USER_AGENT environment variable."
        )

    cik = company["cik"]
    base_url = "https://data.sec.gov/submissions/"

    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
    }

    def fetch_json(url):
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def extract_filings(records, results):
        for i, form in enumerate(records["form"]):
            if form != "10-K":
                continue

            report_date = records["reportDate"][i]

            if not report_date:
                continue

            year = int(report_date[:4])

            if year not in TARGET_YEARS:
                continue

            accession = records["accessionNumber"][i]
            accession_clean = accession.replace("-", "")
            primary_doc = records["primaryDocument"][i]

            filing_url = (
                "https://www.sec.gov/Archives/edgar/data/"
                f"{cik}/{accession_clean}/{primary_doc}"
            )

            filing = {
                "ticker": ticker,
                "company": company["name"],
                "cik": cik,
                "fiscal_year": year,
                "report_date": report_date,
                "accession_number": accession,
                "filing_url": filing_url,
            }

            # Prefer the most recently filed original 10-K
            # if multiple records share the same report year.
            filing_date = records["filingDate"][i]

            current = results.get(year)

            if (
                current is None
                or filing_date > current["_filing_date"]
            ):
                filing["_filing_date"] = filing_date
                results[year] = filing

    url = f"{base_url}CIK{cik:010d}.json"
    data = fetch_json(url)

    results = {}

    extract_filings(
        data["filings"]["recent"],
        results,
    )

    missing = TARGET_YEARS - set(results)

    if missing:
        for archive in data["filings"].get("files", []):
            start = archive["filingFrom"][:4]
            end = archive["filingTo"][:4]

            # Filing dates may fall in the following year.
            if (
                int(end) < min(missing)
                or int(start) > max(missing) + 1
            ):
                continue

            time.sleep(0.5)

            archive_data = fetch_json(
                base_url + archive["name"]
            )

            extract_filings(
                archive_data,
                results,
            )

            missing = TARGET_YEARS - set(results)

            if not missing:
                break

    cleaned = []

    for year in sorted(results):
        filing = results[year].copy()
        filing.pop("_filing_date", None)
        cleaned.append(filing)

    return cleaned

def main():
    all_filings = []

    for ticker, company in COMPANIES.items():
        print(f"Checking {ticker}...")

        filings = get_filings(ticker, company)
        all_filings.extend(filings)

        years_found = {
            item["fiscal_year"] for item in filings
        }

        print(f"  Found: {sorted(years_found)}")

        missing = TARGET_YEARS - years_found

        if missing:
            print(f"  Missing: {sorted(missing)}")

        time.sleep(0.5)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "ticker",
        "company",
        "cik",
        "fiscal_year",
        "report_date",
        "accession_number",
        "filing_url",
    ]

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(all_filings)

    print("\n=== SEC INVENTORY REPORT ===")
    print(f"Companies: {len(COMPANIES)}")
    print(f"Target filings: {len(COMPANIES) * 5}")
    print(f"Filings found: {len(all_filings)}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
