
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.athena_client import run_athena_query


SQL_PATH = (
    PROJECT_ROOT / "sql" / "financial_analytics_v2.sql"
)


st.set_page_config(
    page_title="Company Comparison",
    page_icon="📈",
    layout="wide"
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    sql = SQL_PATH.read_text(encoding="utf-8")
    df = run_athena_query(sql)

    numeric_columns = [
        col for col in df.columns
        if col != "ticker"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    return df


st.title("Multi-Company Financial Analytics")

st.caption(
    "Financial Document Intelligence V2 | "
    "AWS Athena · 14 Companies · 2021–2025"
)

try:
    with st.spinner("Loading financial KPIs from Athena..."):
        df = load_data()
except Exception as error:
    st.error("Unable to retrieve Athena data.")
    st.exception(error)
    st.stop()

if df.empty:
    st.warning("No data available.")
    st.stop()


st.divider()

# --------------------------------------------------
# Filters
# --------------------------------------------------

available_companies = sorted(
    df["ticker"].dropna().unique()
)

selected_companies = st.multiselect(
    "Select companies",
    options=available_companies,
    default=available_companies[:3],
    max_selections=5
)

available_metrics = {
    "Revenue": "revenue",
    "Net Income": "net_income",
    "Total Assets": "total_assets",
    "Operating Margin (%)": "operating_margin_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Revenue Growth (%)": "revenue_growth_pct",
    "Return on Assets (%)": "return_on_assets_pct",
    "Return on Equity (%)": "return_on_equity_pct",
    "Free Cash Flow": "free_cash_flow",
    "Free Cash Flow Margin (%)": "free_cash_flow_margin_pct",
}

selected_metric_label = st.selectbox(
    "Financial indicator",
    options=list(available_metrics)
)

selected_metric = available_metrics[
    selected_metric_label
]

if not selected_companies:
    st.info("Select at least one company.")
    st.stop()

filtered = df[
    df["ticker"].isin(selected_companies)
].copy()


# --------------------------------------------------
# Comparison chart
# --------------------------------------------------

st.subheader(
    f"{selected_metric_label} — Company Comparison"
)

chart = filtered.pivot(
    index="fiscal_year",
    columns="ticker",
    values=selected_metric
)

is_money = selected_metric in {
    "revenue",
    "net_income",
    "total_assets",
    "free_cash_flow"
}

if is_money:
    chart = chart / 1_000_000_000
    y_label = "USD Billions"
else:
    y_label = "Percent (%)"

st.line_chart(
    chart,
    x_label="Fiscal Year",
    y_label=y_label
)


# --------------------------------------------------
# Latest fiscal year comparison
# --------------------------------------------------

st.divider()
st.subheader("Annual Comparison")

selected_year = st.selectbox(
    "Fiscal year",
    options=sorted(
        df["fiscal_year"].dropna().astype(int).unique(),
        reverse=True
    )
)

year_df = filtered[
    filtered["fiscal_year"] == selected_year
].copy()

if not year_df.empty:
    comparison = year_df[
        ["ticker", selected_metric]
    ].sort_values(
        selected_metric,
        ascending=False
    )

    st.dataframe(
        comparison.rename(
            columns={
                "ticker": "Company",
                selected_metric: selected_metric_label
            }
        ),
        hide_index=True,
        use_container_width=True
    )


# --------------------------------------------------
# Data information
# --------------------------------------------------

with st.expander("Data Sources & Methodology"):
    st.markdown(
        """
        **Source:** SEC EDGAR Company Facts (XBRL)

        **Pipeline:**
        SEC API → Python normalization →
        Parquet on Amazon S3 → Amazon Athena →
        Streamlit.

        **Scope:**
        14 companies, fiscal years 2021–2025.

        **Notes:**
        - Missing financial values remain NULL.
        - Financial indicators follow available
          standardized XBRL concepts.
        - Cross-company accounting differences
          can affect comparability.
        - ROA and ROE use year-end balances
          rather than average balances.
        """
    )
