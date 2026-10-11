
from pathlib import Path
import sys

import streamlit as st


# ==================================================
# PROJECT IMPORTS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.sec_rag_pipeline import SECFinancialRAG


# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="SEC AI Financial Assistant",
    page_icon="🤖",
    layout="wide"
)

INDEX_PATH = (
    PROJECT_ROOT
    / "data/processed/rag/sec_index/faiss_full.index"
)

METADATA_PATH = (
    PROJECT_ROOT
    / "data/processed/rag/sec_index/chunks_full.jsonl"
)

# Set to True only after the dry-run test succeeds.
ENABLE_BEDROCK = True


# ==================================================
# LOAD RAG
# ==================================================

@st.cache_resource(show_spinner=False)
def load_rag(use_bedrock: bool):
    return SECFinancialRAG(
        use_bedrock=use_bedrock
    )


# ==================================================
# PAGE HEADER
# ==================================================

st.title("Multi-Company AI Financial Assistant")

st.caption(
    "Financial Document Intelligence V2 | "
    "SEC EDGAR · FAISS · Amazon Bedrock"
)

st.markdown(
    "Ask financial questions across annual "
    "10-K reports from 20 companies "
    "covering fiscal years 2021–2025."
)

if not INDEX_PATH.exists() or not METADATA_PATH.exists():
    st.warning(
        "The SEC FAISS index is not ready yet. "
        "Finish the indexing process before "
        "using this assistant."
    )
    st.stop()

if ENABLE_BEDROCK:
    st.success(
        "AI generation enabled: "
        "Amazon Bedrock Nova Micro."
    )
else:
    st.info(
        "Test mode: semantic retrieval is enabled, "
        "but Bedrock generation is disabled."
    )

st.divider()


# ==================================================
# FILTERS
# ==================================================

COMPANIES = {
    "Microsoft": "MSFT",
    "Apple": "AAPL",
    "Alphabet": "GOOGL",
    "Amazon": "AMZN",
    "Meta": "META",
    "NVIDIA": "NVDA",
    "Tesla": "TSLA",
    "Intel": "INTC",
    "AMD": "AMD",
    "Oracle": "ORCL",
    "Salesforce": "CRM",
    "Adobe": "ADBE",
    "Cisco": "CSCO",
    "Netflix": "NFLX",
    "PayPal": "PYPL",
    "IBM": "IBM",
    "Qualcomm": "QCOM",
    "Texas Instruments": "TXN",
    "Broadcom": "AVGO",
    "Walmart": "WMT",
}

st.subheader("Ask a Financial Question")

col1, col2 = st.columns([2, 1])

with col1:
    company_names = st.multiselect(
        "Select Companies",
        options=list(COMPANIES),
        default=["Microsoft"],
        max_selections=3
    )

with col2:
    year_selection = st.selectbox(
        "Fiscal Year",
        options=[2025, 2024, 2023, 2022, 2021, "All years"]
    )

tickers = [
    COMPANIES[name] for name in company_names
]

fiscal_year = (
    None
    if year_selection == "All years"
    else int(year_selection)
)

question = st.text_area(
    "Your Financial Question",
    value=(
        "What drove Microsoft's revenue "
        "growth in fiscal year 2025?"
    ),
    height=110
)

top_k = st.selectbox(
    "Number of Retrieved Passages",
    options=[3, 5, 7],
    index=1
)

analyze = st.button(
    "Analyze SEC Reports",
    type="primary",
    use_container_width=True
)


# ==================================================
# RAG EXECUTION
# ==================================================

if analyze:

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    if not tickers:
        st.warning(
            "Please select at least one company."
        )
        st.stop()

    try:
        with st.spinner(
            "Searching SEC financial reports..."
        ):
            rag = load_rag(ENABLE_BEDROCK)

            result = rag.ask(
                question=question.strip(),
                tickers=tickers,
                fiscal_year=fiscal_year,
                top_k=top_k
            )

    except Exception as error:
        st.error("RAG execution failed.")
        st.exception(error)
        st.stop()

    # ----------------------------------------------
    # RESPONSE
    # ----------------------------------------------

    st.divider()
    st.subheader("AI Assistant Response")

    if result["mode"] == "bedrock":
        st.markdown(result["answer"])

    elif result["mode"] == "dry_run":
        st.info(
            "Retrieval succeeded. "
            "Bedrock generation is disabled "
            "during this test."
        )

    else:
        st.warning(result["answer"])

    # ----------------------------------------------
    # SOURCES
    # ----------------------------------------------

    st.divider()
    st.subheader("Retrieved SEC Sources")

    st.caption(
        "Sources are SEC filings, identified by "
        "company, fiscal year and accession number."
    )

    for source in result["sources"]:

        label = (
            f"[{source['source_id']}] "
            f"{source['ticker']} "
            f"FY {source['fiscal_year']} "
            f"— Similarity {source['score']:.3f}"
        )

        with st.expander(label):

            st.markdown(
                f"**Company:** {source['ticker']}"
            )

            st.markdown(
                f"**Fiscal year:** "
                f"{source['fiscal_year']}"
            )

            st.markdown(
                f"**SEC accession:** "
                f"{source['accession_number']}"
            )

            st.markdown(
                f"**Document:** {source['document']}"
            )

            st.markdown(
                f"**Original filing:** "
                f"[View on SEC EDGAR]"
                f"({source['source_url']})"
            )

            st.markdown("**Retrieved passage:**")

            st.write(source["text"])

    if result["mode"] == "dry_run":
        with st.expander("Inspect RAG Prompt"):
            st.code(
                result["prompt"],
                language="text"
            )


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown("### Financial AI V2")

    st.markdown(
        """
        **Corpus**
        - 100 annual SEC filings
        - 20 companies
        - Fiscal years 2021–2025

        **Retrieval**
        - Sentence Transformers
        - FAISS IndexFlatIP
        - Company / year filtering

        **Generation**
        - Amazon Nova Micro
        - AWS Bedrock
        - SEC document citations
        """
    )

    st.caption(
        "Python · FAISS · AWS · Streamlit"
    )
