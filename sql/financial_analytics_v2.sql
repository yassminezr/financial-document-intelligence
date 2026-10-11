
-- =========================================================
-- FINANCIAL DOCUMENT INTELLIGENCE V2
-- Multi-Company Financial Analytics
-- AWS Athena / Trino SQL
-- Monetary values expressed in USD
-- =========================================================

WITH financials AS (

    -- Convert financial metrics from rows to columns
    SELECT
        ticker,
        fiscal_year,

        MAX(CASE WHEN metric = 'revenue'
            THEN value_usd END) AS revenue,

        MAX(CASE WHEN metric = 'net_income'
            THEN value_usd END) AS net_income,

        MAX(CASE WHEN metric = 'operating_income'
            THEN value_usd END) AS operating_income,

        MAX(CASE WHEN metric = 'total_assets'
            THEN value_usd END) AS total_assets,

        MAX(CASE WHEN metric = 'total_liabilities'
            THEN value_usd END) AS total_liabilities,

        MAX(CASE WHEN metric = 'equity'
            THEN value_usd END) AS equity,

        MAX(CASE WHEN metric = 'cash'
            THEN value_usd END) AS cash,

        MAX(CASE WHEN metric = 'operating_cash_flow'
            THEN value_usd END) AS operating_cash_flow,

        MAX(CASE WHEN metric = 'capital_expenditures'
            THEN value_usd END) AS capital_expenditures

    FROM financial_intelligence.financial_metrics_v2
    GROUP BY ticker, fiscal_year
),

historical AS (

    -- Retrieve previous fiscal-year values per company
    SELECT
        *,

        LAG(fiscal_year) OVER (
            PARTITION BY ticker
            ORDER BY fiscal_year
        ) AS previous_year,

        LAG(revenue) OVER (
            PARTITION BY ticker
            ORDER BY fiscal_year
        ) AS previous_revenue,

        LAG(net_income) OVER (
            PARTITION BY ticker
            ORDER BY fiscal_year
        ) AS previous_net_income,

        LAG(total_assets) OVER (
            PARTITION BY ticker
            ORDER BY fiscal_year
        ) AS previous_assets

    FROM financials
)

SELECT
    ticker,
    fiscal_year,

    -- =============================================
    -- BASE FINANCIAL METRICS
    -- =============================================

    revenue,
    net_income,
    operating_income,
    total_assets,
    total_liabilities,
    equity,
    cash,
    operating_cash_flow,
    capital_expenditures,

    -- =============================================
    -- 1. REVENUE GROWTH (%)
    -- =============================================

    CASE
        WHEN previous_year = fiscal_year - 1
        THEN ROUND(
            100.0 * (revenue - previous_revenue)
            / NULLIF(previous_revenue, 0),
            2
        )
    END AS revenue_growth_pct,

    -- =============================================
    -- 2. NET INCOME GROWTH (%)
    -- =============================================

    CASE
        WHEN previous_year = fiscal_year - 1
        THEN ROUND(
            100.0 * (net_income - previous_net_income)
            / NULLIF(ABS(previous_net_income), 0),
            2
        )
    END AS net_income_growth_pct,

    -- =============================================
    -- 3. TOTAL ASSETS GROWTH (%)
    -- =============================================

    CASE
        WHEN previous_year = fiscal_year - 1
        THEN ROUND(
            100.0 * (total_assets - previous_assets)
            / NULLIF(previous_assets, 0),
            2
        )
    END AS assets_growth_pct,

    -- =============================================
    -- 4. NET PROFIT MARGIN (%)
    -- =============================================

    ROUND(
        100.0 * net_income
        / NULLIF(revenue, 0),
        2
    ) AS net_profit_margin_pct,

    -- =============================================
    -- 5. OPERATING MARGIN (%)
    -- =============================================

    ROUND(
        100.0 * operating_income
        / NULLIF(revenue, 0),
        2
    ) AS operating_margin_pct,

    -- =============================================
    -- 6. RETURN ON ASSETS (%)
    -- Simplified: using end-of-year assets
    -- =============================================

    ROUND(
        100.0 * net_income
        / NULLIF(total_assets, 0),
        2
    ) AS return_on_assets_pct,

    -- =============================================
    -- 7. RETURN ON EQUITY (%)
    -- Simplified: using end-of-year equity
    -- =============================================

    ROUND(
        100.0 * net_income
        / NULLIF(equity, 0),
        2
    ) AS return_on_equity_pct,

    -- =============================================
    -- 8. LIABILITIES TO EQUITY
    -- =============================================

    ROUND(
        1.0 * total_liabilities
        / NULLIF(equity, 0),
        2
    ) AS liabilities_to_equity,

    -- =============================================
    -- 9. FREE CASH FLOW (USD)
    -- =============================================

    (
        operating_cash_flow - capital_expenditures
    ) AS free_cash_flow,

    -- =============================================
    -- 10. FREE CASH FLOW MARGIN (%)
    -- =============================================

    ROUND(
        100.0 * (
            operating_cash_flow - capital_expenditures
        )
        / NULLIF(revenue, 0),
        2
    ) AS free_cash_flow_margin_pct,

    -- =============================================
    -- 11. OPERATING CASH FLOW MARGIN (%)
    -- =============================================

    ROUND(
        100.0 * operating_cash_flow
        / NULLIF(revenue, 0),
        2
    ) AS operating_cash_flow_margin_pct,

    -- =============================================
    -- 12. CASH TO ASSETS (%)
    -- =============================================

    ROUND(
        100.0 * cash
        / NULLIF(total_assets, 0),
        2
    ) AS cash_to_assets_pct

FROM historical

ORDER BY ticker, fiscal_year;
