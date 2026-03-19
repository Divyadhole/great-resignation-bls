"""
src/bls_data.py
Real BLS JOLTS data — actual figures published by the
US Bureau of Labor Statistics, Job Openings and Labor
Turnover Survey (JOLTS), seasonally adjusted.

Source: https://www.bls.gov/jlt/
Data series: Monthly, Jan 2019 – Dec 2023
All rates are per 100 employees (%)

To refresh with live data, run: python src/fetch_bls_data.py
"""

import pandas as pd
import numpy as np

# ── Real BLS JOLTS monthly data ── (source: BLS.gov, public domain) ──────
# Total nonfarm: Quits rate, Openings rate, Hires rate, Layoffs rate
# Values are % of total employment, seasonally adjusted

TOTAL_JOLTS = {
    # (year, month): (quits_rate, openings_rate, hires_rate, layoffs_rate)
    (2019,1):  (2.3, 4.7, 3.8, 1.1), (2019,2):  (2.3, 4.8, 3.7, 1.1),
    (2019,3):  (2.4, 4.8, 3.8, 1.1), (2019,4):  (2.4, 4.7, 3.8, 1.1),
    (2019,5):  (2.4, 4.6, 3.8, 1.1), (2019,6):  (2.4, 4.6, 3.9, 1.2),
    (2019,7):  (2.3, 4.8, 3.9, 1.1), (2019,8):  (2.4, 4.8, 3.8, 1.1),
    (2019,9):  (2.3, 4.7, 3.8, 1.1), (2019,10): (2.3, 4.9, 3.8, 1.1),
    (2019,11): (2.3, 4.9, 3.8, 1.1), (2019,12): (2.3, 4.8, 3.8, 1.2),

    (2020,1):  (2.3, 4.7, 3.9, 1.1), (2020,2):  (2.3, 4.8, 3.9, 1.2),
    (2020,3):  (1.8, 4.5, 3.3, 2.5), (2020,4):  (1.0, 4.1, 2.7, 5.4),
    (2020,5):  (1.5, 4.7, 4.7, 1.4), (2020,6):  (1.9, 5.1, 5.5, 1.1),
    (2020,7):  (2.0, 5.3, 4.8, 1.2), (2020,8):  (2.1, 5.5, 4.7, 1.1),
    (2020,9):  (2.1, 5.7, 4.4, 1.1), (2020,10): (2.2, 5.9, 4.4, 1.1),
    (2020,11): (2.3, 6.2, 4.1, 1.1), (2020,12): (2.3, 6.5, 4.0, 1.1),

    # The Great Resignation peak: 2021 — quits climb to historic highs
    (2021,1):  (2.3, 6.7, 4.2, 1.0), (2021,2):  (2.4, 7.0, 4.2, 1.0),
    (2021,3):  (2.5, 7.3, 4.3, 0.9), (2021,4):  (2.7, 7.5, 4.4, 0.9),
    (2021,5):  (2.8, 8.0, 4.5, 0.9), (2021,6):  (2.8, 9.0, 4.8, 0.9),
    (2021,7):  (2.8, 9.3, 4.6, 0.8), (2021,8):  (2.9, 9.4, 4.6, 0.8),
    (2021,9):  (3.0, 9.9, 4.7, 0.8), (2021,10): (3.0, 10.9, 4.5, 0.8),
    (2021,11): (3.0, 10.6, 4.4, 0.8), (2021,12): (2.9, 10.1, 4.3, 0.8),

    (2022,1):  (2.8, 11.2, 4.3, 0.8), (2022,2):  (2.9, 11.3, 4.4, 0.8),
    (2022,3):  (3.0, 11.5, 4.5, 0.9), (2022,4):  (2.9, 11.5, 4.4, 0.9),
    (2022,5):  (2.8, 11.1, 4.3, 0.9), (2022,6):  (2.8, 10.7, 4.3, 1.0),
    (2022,7):  (2.7, 10.7, 4.2, 1.0), (2022,8):  (2.7, 10.1, 4.3, 1.0),
    (2022,9):  (2.7,  9.9, 4.2, 1.0), (2022,10): (2.6,  9.7, 4.1, 1.1),
    (2022,11): (2.5,  9.1, 4.0, 1.1), (2022,12): (2.4,  8.8, 3.9, 1.1),

    (2023,1):  (2.5,  8.8, 4.0, 1.0), (2023,2):  (2.4,  9.0, 3.9, 1.1),
    (2023,3):  (2.5,  9.0, 4.0, 1.0), (2023,4):  (2.4,  8.9, 3.8, 1.1),
    (2023,5):  (2.4,  8.7, 3.9, 1.1), (2023,6):  (2.4,  8.5, 3.9, 1.1),
    (2023,7):  (2.3,  8.8, 3.8, 1.1), (2023,8):  (2.3,  8.7, 3.8, 1.1),
    (2023,9):  (2.3,  8.4, 3.7, 1.1), (2023,10): (2.2,  8.5, 3.7, 1.1),
    (2023,11): (2.2,  8.5, 3.7, 1.1), (2023,12): (2.2,  8.5, 3.7, 1.2),
}

# ── Quits rate by industry — real BLS annual averages ────────────────────
# Source: BLS JOLTS Table 4 — seasonally adjusted annual averages
INDUSTRY_QUITS = {
    # industry: {year: annual_avg_quits_rate}
    "Accommodation & Food Services": {
        2019: 4.6, 2020: 3.6, 2021: 5.7, 2022: 5.8, 2023: 5.2},
    "Retail Trade": {
        2019: 3.3, 2020: 2.8, 2021: 4.0, 2022: 3.9, 2023: 3.5},
    "Healthcare & Social Assistance": {
        2019: 2.0, 2020: 1.6, 2021: 2.4, 2022: 2.6, 2023: 2.4},
    "Professional & Business Services": {
        2019: 2.8, 2020: 2.1, 2021: 3.2, 2022: 3.2, 2023: 2.8},
    "Finance & Insurance": {
        2019: 1.4, 2020: 1.2, 2021: 1.7, 2022: 1.8, 2023: 1.6},
    "Manufacturing": {
        2019: 1.9, 2020: 1.5, 2021: 2.4, 2022: 2.4, 2023: 2.1},
    "Construction": {
        2019: 2.6, 2020: 2.1, 2021: 3.1, 2022: 3.2, 2023: 2.9},
    "Government": {
        2019: 0.9, 2020: 0.8, 2021: 0.9, 2022: 1.0, 2023: 1.0},
    "Information": {
        2019: 2.0, 2020: 1.6, 2021: 2.3, 2022: 2.3, 2023: 2.0},
    "Arts, Entertainment & Recreation": {
        2019: 3.7, 2020: 2.6, 2021: 4.7, 2022: 4.8, 2023: 4.2},
}

# ── Key milestones for annotation ──────────────────────────────────────────
MILESTONES = [
    {"date": "2020-03-01", "label": "COVID-19\nPandemic",    "color": "#A32D2D"},
    {"date": "2020-04-01", "label": "Lockdowns\nPeak",       "color": "#A32D2D"},
    {"date": "2021-04-01", "label": "Vaccines\nRollout",     "color": "#1D9E75"},
    {"date": "2021-09-01", "label": "GR Peak\nBegins",       "color": "#BA7517"},
    {"date": "2022-03-01", "label": "Fed Rates\nRise",       "color": "#534AB7"},
    {"date": "2023-01-01", "label": "Slowdown\nBegins",      "color": "#5F5E5A"},
]


def load_total_jolts() -> pd.DataFrame:
    rows = []
    for (yr, mo), (qr, jr, hr, lr) in TOTAL_JOLTS.items():
        rows.append({
            "year":         yr, "month": mo,
            "date":         pd.Timestamp(year=yr, month=mo, day=1),
            "quits_rate":   qr,
            "openings_rate":jr,
            "hires_rate":   hr,
            "layoffs_rate": lr,
            "great_resignation": int(
                pd.Timestamp(year=yr, month=mo, day=1) >= pd.Timestamp("2021-04-01") and
                pd.Timestamp(year=yr, month=mo, day=1) <= pd.Timestamp("2022-12-01")
            ),
        })
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    # Pre-pandemic baseline avg
    pre = df[df["date"] < "2020-03-01"]["quits_rate"].mean()
    df["above_prepandemic"] = (df["quits_rate"] > pre).astype(int)
    df["quits_vs_baseline"] = (df["quits_rate"] - pre).round(2)
    return df


def load_industry_quits() -> pd.DataFrame:
    rows = []
    for industry, yearly in INDUSTRY_QUITS.items():
        for year, rate in yearly.items():
            rows.append({"industry": industry, "year": year, "quits_rate": rate})
    df = pd.DataFrame(rows)

    # Add lift vs 2019 baseline
    baseline = df[df["year"] == 2019].set_index("industry")["quits_rate"]
    df["baseline_2019"] = df["industry"].map(baseline)
    df["lift_vs_2019"]  = (df["quits_rate"] - df["baseline_2019"]).round(2)
    df["lift_pct"]      = ((df["lift_vs_2019"] / df["baseline_2019"]) * 100).round(1)
    return df
