
from pathlib import Path
import sys

import streamlit as st


# ==================================================
# PROJECT IMPORTS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.rag_pipeline import FinancialRAG


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="AI Financial Assistant",
    page_icon="🤖",
    layout="wide"
)


# ==================================================
# RAG PIPELINE
# ==================================================

@st.cache_resource(show_spinner=False)
def load_rag():
    """
    Load Sentence Transformers and FAISS once.

    Bedrock is disabled while AWS account
    verification is pending.
    """
    return FinancialRAG(use_bedrock=True )


# ==================================================
# PAGE HEADER
# ==================================================

st.title("AI Financial Assistant")

st.caption(
    "Financial Document Intelligence | "
    "Sentence Transformers · FAISS · Amazon Bedrock"
)

st.success(
    "AI Assistant is operational. "
    "Financial questions are answered using "
    "FAISS retrieval and Amazon Nova Micro "
    "via AWS Bedrock."
)

st.divider()


# ==================================================
# QUESTION CONFIGURATION
# ==================================================

st.subheader("Ask a Financial Question")

left_col, right_col = st.columns([2, 1])

with left_col:
    year_filter = st.selectbox(
        "Fiscal Year",
        options=[
            2025,
            2024,
            2023,
            "All years"
        ],
        index=0
    )

with right_col:
    top_k = st.selectbox(
        "Number of Sources",
        options=[3, 5, 7, 10],
        index=1
    )

fiscal_year = (
    None
    if year_filter == "All years"
    else int(year_filter)
)

question = st.text_area(
    "Your Financial Question",
    value=(
        "What drove Microsoft's revenue "
        "growth in fiscal year 2025?"
    ),
    height=110,
    placeholder=(
        "Ask about revenue growth, "
        "cloud performance, AI investments..."
    )
)


# ==================================================
# ANALYZE BUTTON
# ==================================================

analyze = st.button(
    "Analyze Financial Documents",
    type="primary",
    use_container_width=True
)


# ==================================================
# RAG EXECUTION
# ==================================================

if analyze:

    if not question.strip():
        st.warning(
            "Please enter a financial question."
        )
        st.stop()

    try:
        with st.spinner(
            "Searching financial documents..."
        ):
            rag = load_rag()

            result = rag.ask(
                question=question.strip(),
                fiscal_year=fiscal_year,
                top_k=top_k
            )

    except Exception as error:
        st.error(
            "An error occurred during RAG execution."
        )
        st.exception(error)
        st.stop()

    # ----------------------------------------------
    # Retrieval status
    # ----------------------------------------------

    if result["sources"]:
        st.success(
            f"Semantic retrieval completed — "
            f"{len(result['sources'])} passages found."
        )
    else:
        st.warning(
            "No relevant document passages found."
        )

    st.divider()

    # ----------------------------------------------
    # AI response
    # ----------------------------------------------

    st.subheader("AI Assistant Response")

    if result["mode"] == "dry_run":
        st.warning(
            "LLM generation is currently disabled. "
            "FAISS has retrieved relevant passages, "
            "and the RAG prompt is ready for Bedrock."
        )

        st.markdown(
            "**The following sources will be used "
            "to generate the final answer.**"
        )

    elif result["mode"] == "bedrock":
        st.markdown(result["answer"])

    else:
        st.info(result["answer"])

    # ----------------------------------------------
    # Retrieved sources
    # ----------------------------------------------

    st.divider()

    st.subheader("Retrieved Financial Sources")

    st.caption(
        "Each passage includes its original "
        "financial report, page number "
        "and semantic similarity score."
    )

    for index, source in enumerate(
        result["sources"],
        start=1
    ):

        document = source["document"]
        page = source["page"]
        score = source["score"]
        year = source["fiscal_year"]

        source_title = (
            f"Source {index} | "
            f"{document} | "
            f"Page {page} | "
            f"Score {score:.3f}"
        )

        with st.expander(
            source_title,
            expanded=(index == 1)
        ):

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Document**")
                st.write(document)

            with col2:
                st.markdown("**Fiscal Year**")
                st.write(year)

            with col3:
                st.markdown("**Page Number**")
                st.write(page)

            st.markdown("**Retrieved Passage**")

            st.write(
                source.get(
                    "text",
                    "Passage text unavailable."
                )
            )

            st.caption(
                f"Cosine similarity: {score:.4f}"
            )

    # ----------------------------------------------
    # Prompt inspection
    # ----------------------------------------------

    if result["mode"] == "dry_run":
        st.divider()

        with st.expander(
            "Technical Details — RAG Prompt"
        ):

            st.caption(
                "This prompt combines the user's "
                "question with the retrieved "
                "financial document excerpts."
            )

            st.code(
                result.get("prompt", ""),
                language="text"
            )

            st.caption(
                "No Amazon Bedrock inference "
                "request was made."
            )


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown("## Financial AI")

    st.caption(
        "Document Intelligence Platform"
    )

    st.divider()

    st.markdown("### Architecture")

    st.markdown(
        """
        **Document Processing**
        - Microsoft Annual Reports
        - PDF text extraction
        - Text chunking

        **Semantic Retrieval**
        - Sentence Transformers
        - 384-dimensional embeddings
        - FAISS IndexFlatIP
        - Fiscal year filtering

        **AI Generation**
        - Amazon Bedrock
        - Amazon Nova Micro
        - Grounded responses
        - Document citations
        """
    )

    st.divider()

    st.markdown("### Available Reports")

    st.write("Microsoft — FY 2023")
    st.write("Microsoft — FY 2024")
    st.write("Microsoft — FY 2025")

    st.divider()

    st.caption(
        "Python · AWS · FAISS · Streamlit"
    )
