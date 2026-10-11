# Financial Document Intelligence — AWS & AI

An end-to-end Financial Data Engineering and RAG platform for ingesting, analyzing, and querying SEC annual financial filings.

## Project Overview

The platform combines two complementary pipelines:

**Financial Analytics:** SEC Company Facts (XBRL) → Python normalization and data quality → Amazon S3 (Parquet) → AWS Glue Data Catalog → Amazon Athena → Streamlit.

**Document Intelligence:** SEC 10-K filings → HTML text extraction → Chunking → Sentence Transformers → FAISS → Amazon Bedrock (Nova Micro) → Streamlit.

## Key Results

| Metric | Result |
|---|---|
| SEC annual filings ingested | 100 |
| Companies in document corpus | 20 |
| Fiscal years | 2021–2025 |
| Raw filing corpus size | 297.35 MiB |
| Extracted text | 34,878,546 characters |
| Text chunks indexed | 33,400 |
| Embedding dimensions | 384 |
| FAISS index | IndexFlatIP |
| Index build time | 2,116.76 seconds (CPU) |
| Companies in structured analytics | 14 |
| Normalized financial observations | 590 |
| XBRL metric-slot coverage | 93.7% |
| Financial metric types | 9 |
| Calculated financial KPIs | 12 |
| Automated retrieval checks | 8/8 passed |
| Mean retrieval latency | 35 ms |

Retrieval latency excludes model and index loading, LLM inference, and network overhead.

## Technology Stack

Python, Pandas, PyArrow, Amazon S3, AWS Glue, Amazon Athena, Amazon Bedrock, Boto3, SEC EDGAR API, XBRL, BeautifulSoup, Sentence Transformers, FAISS, and Streamlit.

## Main Features

- Automated SEC filing discovery and ingestion with SHA-256-based duplicate detection.
- Structured XBRL financial data extraction and normalization.
- Data quality checks and financial analytics using Athena SQL.
- Interactive multi-company financial comparisons.
- Semantic search across 100 SEC annual reports.
- Company and fiscal-year filtering.
- RAG-based financial question answering with source references.
- Streamlit analytics dashboards and AI assistant.

## Repository Structure

- `src/ingestion/` — SEC filing discovery and ingestion
- `src/financial_data/` — XBRL ingestion, normalization, and Parquet publishing
- `src/analytics/` — Athena query client
- `src/rag/` — Document extraction, embeddings, FAISS, and Bedrock integration
- `sql/` — Financial analytics queries
- `app/` — Streamlit application
- `tests/` — Retrieval evaluation

## Local Setup

Use Python 3.12 and install the project's required dependencies, including a compatible CPU version of PyTorch.

Configure AWS CLI profile `financial-ai` with the required least-privilege access to S3, Glue, Athena, and Bedrock. Set `SEC_USER_AGENT` to a valid contact identifier when accessing SEC APIs.

To launch the application:

```bash
python -m streamlit run app/dashboard.py
```

External AWS services require network connectivity and may incur charges.

## Evaluation and Limitations

Eight automated retrieval scenarios passed their functional checks for metadata filtering and result count. These tests do not establish answer accuracy or semantic Recall@5.

Structured financial analytics currently covers 14 of the 20 companies in the document corpus. Metric availability varies by company and year. Accounting concept mappings, historical observations, and fiscal-period comparability require additional auditing for production-grade analysis.

FAISS IndexFlatIP performs exact vector search, with metadata filters applied after retrieval. This is suitable for the current prototype but may be inefficient at substantially larger scale.

RAG-generated citations refer to SEC filings and retrieved passages. Citation correctness is not yet independently verified. The solution is a portfolio prototype, not an investment advisory system.