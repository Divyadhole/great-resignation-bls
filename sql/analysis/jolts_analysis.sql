-- ============================================================
-- sql/analysis/jolts_analysis.sql
-- Great Resignation — SQL Analysis on Real BLS JOLTS Data
-- ============================================================


-- 1. Phase comparison: Pre-pandemic vs COVID vs GR vs Recovery
SELECT
    CASE
        WHEN date < '2020-03-01'                          THEN '1. Pre-pandemic (2019–Feb 2020)'
        WHEN date BETWEEN '2020-03-01' AND '2020-11-30'  THEN '2. COVID shock (Mar–Nov 2020)'
        WHEN date BETWEEN '2020-12-01' AND '2021-03-31'  THEN '3. Transition (Dec 2020–Mar 2021)'
        WHEN date BETWEEN '2021-04-01' AND '2022-12-31'  THEN '4. Great Resignation (Apr 2021–Dec 2022)'
        ELSE                                                   '5. Recovery (2023)'
    END AS phase,
    COUNT(*)                               AS months,
    ROUND(AVG(quits_rate), 3)             AS avg_quits_rate,
    ROUND(MAX(quits_rate), 3)             AS peak_quits_rate,
    ROUND(AVG(openings_rate), 3)          AS avg_openings_rate,
    ROUND(AVG(hires_rate), 3)             AS avg_hires_rate,
    ROUND(AVG(layoffs_rate), 3)           AS avg_layoffs_rate
FROM jolts_total
GROUP BY phase
ORDER BY phase;


-- 2. Rolling 3-month average quit rate (smoothed trend)
SELECT
    date, year, month,
    quits_rate,
    ROUND(AVG(quits_rate) OVER (
        ORDER BY date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 3) AS rolling_3m_avg,
    ROUND(quits_rate - LAG(quits_rate, 12) OVER (ORDER BY date), 3)
          AS vs_same_month_prev_year,
    above_prepandemic
FROM jolts_total
ORDER BY date;


-- 3. Month where Great Resignation peaked
SELECT
    date, quits_rate, openings_rate,
    ROUND(quits_rate + openings_rate, 2) AS combined_pressure_index,
    RANK() OVER (ORDER BY quits_rate DESC) AS quits_rank,
    RANK() OVER (ORDER BY openings_rate DESC) AS openings_rank
FROM jolts_total
ORDER BY quits_rate DESC
LIMIT 10;


-- 4. Year-over-year change in quits rate
WITH yearly AS (
    SELECT year,
           ROUND(AVG(quits_rate), 3)    AS avg_quits,
           ROUND(AVG(openings_rate), 3) AS avg_openings,
           ROUND(AVG(hires_rate), 3)    AS avg_hires
    FROM jolts_total
    GROUP BY year
)
SELECT
    year, avg_quits, avg_openings, avg_hires,
    ROUND(avg_quits - LAG(avg_quits) OVER (ORDER BY year), 3)
          AS yoy_quits_change,
    ROUND(100.0 * (avg_quits - LAG(avg_quits) OVER (ORDER BY year))
          / NULLIF(LAG(avg_quits) OVER (ORDER BY year), 0), 1)
          AS yoy_quits_change_pct
FROM yearly ORDER BY year;


-- 5. Industry quits: who led the Great Resignation?
SELECT
    industry,
    MAX(CASE WHEN year=2019 THEN quits_rate END) AS rate_2019,
    MAX(CASE WHEN year=2020 THEN quits_rate END) AS rate_2020,
    MAX(CASE WHEN year=2021 THEN quits_rate END) AS rate_2021,
    MAX(CASE WHEN year=2022 THEN quits_rate END) AS rate_2022,
    MAX(CASE WHEN year=2023 THEN quits_rate END) AS rate_2023,
    ROUND(MAX(CASE WHEN year=2021 THEN quits_rate END) -
          MAX(CASE WHEN year=2019 THEN quits_rate END), 2) AS gr_lift,
    ROUND(100.0 * (MAX(CASE WHEN year=2021 THEN quits_rate END) -
          MAX(CASE WHEN year=2019 THEN quits_rate END)) /
          NULLIF(MAX(CASE WHEN year=2019 THEN quits_rate END), 0), 1)
          AS gr_lift_pct,
    RANK() OVER (ORDER BY
        MAX(CASE WHEN year=2021 THEN quits_rate END) -
        MAX(CASE WHEN year=2019 THEN quits_rate END)
        DESC) AS impact_rank
FROM industry_quits
GROUP BY industry
ORDER BY gr_lift DESC;


-- 6. Wage pressure index: highest pressure months
SELECT
    date, year, month,
    quits_rate,
    openings_rate,
    ROUND(quits_rate * 0.6 + openings_rate * 0.4, 3) AS wage_pressure_index,
    CASE
        WHEN quits_rate * 0.6 + openings_rate * 0.4 >= 8.5 THEN 'Extreme'
        WHEN quits_rate * 0.6 + openings_rate * 0.4 >= 7.0 THEN 'High'
        WHEN quits_rate * 0.6 + openings_rate * 0.4 >= 5.5 THEN 'Moderate'
        ELSE 'Low'
    END AS pressure_tier
FROM jolts_total
ORDER BY wage_pressure_index DESC
LIMIT 15;
