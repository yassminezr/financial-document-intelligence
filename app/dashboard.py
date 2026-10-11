
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.athena_client import run_athena_query


SQL_PATH = (
    PROJECT_ROOT / "sql" / "financial_analytics.sql"
)


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Financial Document Intelligence",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# Data loading
# --------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def load_financial_data() -> pd.DataFrame:
    """
    Load financial KPIs from AWS Athena.
    Cache results for 1 hour.
    """

    sql = SQL_PATH.read_text(encoding="utf-8")

    df = run_athena_query(sql)

    if df.empty:
        return df

    numeric_columns = [
        "fiscal_year",
        "revenue",
        "net_income",
        "total_assets",
        "revenue_growth_pct",
        "net_income_growth_pct",
        "assets_growth_pct",
        "net_profit_margin_pct"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.sort_values("fiscal_year")

    return df


def format_billions(value):
    """Convert millions USD to billions USD."""

    if pd.isna(value):
        return "N/A"

    return f"${value / 1000:,.2f}B"


def format_percent(value):
    if pd.isna(value):
        return "N/A"

    return f"{value:+.2f}%"


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

st.title("Financial Document Intelligence")

st.caption(
    "AWS-powered Financial Analytics | "
    "Microsoft Annual Reports 2023–2025"
)

st.divider()

st.subheader("Financial Performance Overview")

st.markdown(
    "Explore Microsoft's financial performance "
    "using structured financial data processed "
    "and queried through Amazon Athena."
)


try:
    with st.spinner("Loading financial data from Athena..."):
        df = load_financial_data()

except Exception as error:
    st.error("Unable to load financial data from Athena.")
    st.exception(error)
    st.stop()


if df.empty:
    st.warning("No financial data available.")
    st.stop()


# --------------------------------------------------
# Year selection
# --------------------------------------------------

available_years = sorted(
    df["fiscal_year"].dropna().astype(int).unique(),
    reverse=True
)

selected_year = st.selectbox(
    "Select fiscal year",
    options=available_years
)

current = df[
    df["fiscal_year"] == selected_year
].iloc[0]


# --------------------------------------------------
# Financial KPI cards
# --------------------------------------------------

st.subheader(f"Key Financial Metrics — FY {selected_year}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Revenue",
        value=format_billions(current["revenue"]),
        delta=(
            None
            if pd.isna(current["revenue_growth_pct"])
            else format_percent(
                current["revenue_growth_pct"]
            ) + " YoY"
        )
    )

with col2:
    st.metric(
        label="Net Income",
        value=format_billions(current["net_income"]),
        delta=(
            None
            if pd.isna(current["net_income_growth_pct"])
            else format_percent(
                current["net_income_growth_pct"]
            ) + " YoY"
        )
    )

with col3:
    st.metric(
        label="Total Assets",
        value=format_billions(current["total_assets"]),
        delta=(
            None
            if pd.isna(current["assets_growth_pct"])
            else format_percent(
                current["assets_growth_pct"]
            ) + " YoY"
        )
    )


# --------------------------------------------------
# Financial evolution
# --------------------------------------------------

st.divider()
st.subheader("Financial Evolution")

chart_df = df[
    [
        "fiscal_year",
        "revenue",
        "net_income",
        "total_assets"
    ]
].copy()

for column in [
    "revenue",
    "net_income",
    "total_assets"
]:
    chart_df[column] = chart_df[column] / 1000

chart_df = chart_df.rename(
    columns={
        "revenue": "Revenue",
        "net_income": "Net Income",
        "total_assets": "Total Assets"
    }
)

chart_df = chart_df.set_index("fiscal_year")

st.line_chart(
    chart_df,
    x_label="Fiscal Year",
    y_label="USD Billions"
)

st.caption(
    "Financial values expressed in billions "
    "of US dollars."
)


# --------------------------------------------------
# Profitability and growth
# --------------------------------------------------

st.divider()
st.subheader("Growth & Profitability")

left, right = st.columns(2)

with left:
    st.markdown("**Revenue Growth (%)**")

    growth_df = df[
        ["fiscal_year", "revenue_growth_pct"]
    ].copy()

    growth_df = growth_df.dropna(
        subset=["revenue_growth_pct"]
    )

    growth_df = growth_df.set_index("fiscal_year")

    st.bar_chart(
        growth_df,
        x_label="Fiscal Year",
        y_label="Year-over-Year Growth (%)"
    )

with right:
    st.markdown("**Net Profit Margin (%)**")

    margin_df = df[
        ["fiscal_year", "net_profit_margin_pct"]
    ].copy()

    margin_df = margin_df.set_index("fiscal_year")

    st.line_chart(
        margin_df,
        x_label="Fiscal Year",
        y_label="Net Profit Margin (%)"
    )


# --------------------------------------------------
# Detailed KPI table
# --------------------------------------------------

st.divider()
st.subheader("Financial KPI Comparison")

display_df = df.copy()

display_df = display_df.rename(
    columns={
        "fiscal_year": "Fiscal Year",
        "revenue": "Revenue (USD M)",
        "net_income": "Net Income (USD M)",
        "total_assets": "Total Assets (USD M)",
        "revenue_growth_pct": "Revenue Growth (%)",
        "net_income_growth_pct": "Net Income Growth (%)",
        "assets_growth_pct": "Assets Growth (%)",
        "net_profit_margin_pct": "Net Profit Margin (%)"
    }
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# Data lineage
# --------------------------------------------------

st.divider()

with st.expander("Data Sources & Architecture"):
    st.markdown(
        """
        **Source documents**
        - Microsoft Annual Reports: 2023, 2024, 2025

        **Data pipeline**
        1. PDF ingestion into Amazon S3
        2. Financial metric extraction using Python
        3. Data validation and normalization
        4. Parquet storage in Amazon S3
        5. SQL analytics using Amazon Athena
        6. Interactive visualization with Streamlit

        **Financial metrics**
        - Revenue
        - Net Income
        - Total Assets
        - Year-over-Year Growth
        - Net Profit Margin

        **Data units:** USD millions in Athena,
        converted to USD billions for KPI cards
        and trend visualizations.
        """
    )


st.caption(
    "Financial Document Intelligence | "
    "Python · AWS S3 · Athena · Streamlit"
)
