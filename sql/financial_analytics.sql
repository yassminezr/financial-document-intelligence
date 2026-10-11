
-- Financial Document Intelligence
-- Microsoft Financial Analytics 2023–2025
-- Values expressed in millions USD

WITH yearly_metrics AS (
    SELECT
        fiscal_year,
        MAX(CASE WHEN metric = 'revenue'
            THEN value_millions END) AS revenue,
        MAX(CASE WHEN metric = 'net_income'
            THEN value_millions END) AS net_income,
        MAX(CASE WHEN metric = 'total_assets'
            THEN value_millions END) AS total_assets
    FROM financial_intelligence.financial_metrics
    GROUP BY fiscal_year
),

previous_year AS (
    SELECT
        *,
        LAG(revenue) OVER (
            ORDER BY fiscal_year
        ) AS previous_revenue,

        LAG(net_income) OVER (
            ORDER BY fiscal_year
        ) AS previous_net_income,

        LAG(total_assets) OVER (
            ORDER BY fiscal_year
        ) AS previous_total_assets
    FROM yearly_metrics
)

SELECT
    fiscal_year,
    revenue,
    net_income,
    total_assets,

    ROUND(
        100.0 * (revenue - previous_revenue)
        / NULLIF(previous_revenue, 0), 2
    ) AS revenue_growth_pct,

    ROUND(
        100.0 * (net_income - previous_net_income)
        / NULLIF(ABS(previous_net_income), 0), 2
    ) AS net_income_growth_pct,

    ROUND(
        100.0 * (total_assets - previous_total_assets)
        / NULLIF(previous_total_assets, 0), 2
    ) AS assets_growth_pct,

    ROUND(
        100.0 * net_income / NULLIF(revenue, 0), 2
    ) AS net_profit_margin_pct

FROM previous_year
ORDER BY fiscal_year;
