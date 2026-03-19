"""
src/fetch_bls_data.py
Fetches REAL data from the BLS Public Data API v2.
No API key required for up to 25 series per request.

BLS JOLTS (Job Openings and Labor Turnover Survey) series:
  - Quits rate by industry
  - Job openings rate by industry
  - Layoffs rate by industry
  - Hires rate by industry

Series ID format: JTS[industry][size][rateorLevel][dataelement][seasonal]
All Industries total: JTS000000000000000QUR (Quits Rate)
"""

import requests
import pandas as pd
import json
import time
from pathlib import Path

BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# ── JOLTS Series IDs — real BLS codes ─────────────────────────────────────
# Format: JTS + industry_code + "00000" + seasonal + rate_type
SERIES = {
    # Total nonfarm — all 4 measures
    "total_quits_rate":     "JTS000000000000000QUR",
    "total_openings_rate":  "JTS000000000000000JOR",
    "total_hires_rate":     "JTS000000000000000HIR",
    "total_layoffs_rate":   "JTS000000000000000LDR",

    # Quits rate by major industry
    "quits_accommodation":  "JTS7200000000000QUR",   # Accommodation & Food Services
    "quits_retail":         "JTS4400000000000QUR",   # Retail Trade
    "quits_healthcare":     "JTS6200000000000QUR",   # Health Care & Social Assistance
    "quits_finance":        "JTS5200000000000QUR",   # Finance & Insurance
    "quits_manufacturing":  "JTS3000000000000QUR",   # Manufacturing
    "quits_professional":   "JTS5400000000000QUR",   # Professional & Business Services
    "quits_construction":   "JTS2300000000000QUR",   # Construction
    "quits_government":     "JTS9000000000000QUR",   # Government

    # Job openings rate by industry
    "openings_accommodation":"JTS7200000000000JOR",
    "openings_retail":       "JTS4400000000000JOR",
    "openings_healthcare":   "JTS6200000000000JOR",
    "openings_professional": "JTS5400000000000JOR",
    "openings_manufacturing":"JTS3000000000000JOR",
}

INDUSTRY_LABELS = {
    "accommodation":  "Accommodation & Food Services",
    "retail":         "Retail Trade",
    "healthcare":     "Healthcare & Social Assistance",
    "finance":        "Finance & Insurance",
    "manufacturing":  "Manufacturing",
    "professional":   "Professional & Business Services",
    "construction":   "Construction",
    "government":     "Government",
}


def fetch_series(series_ids: list, start_year: str = "2019", end_year: str = "2024") -> dict:
    """Fetch BLS time series data. Returns dict of {series_id: DataFrame}."""
    payload = {
        "seriesid":  series_ids,
        "startyear": start_year,
        "endyear":   end_year,
        "calculations": True,
        "annualaverage": True,
    }

    print(f"  Fetching {len(series_ids)} series from BLS API...")
    resp = requests.post(BLS_API, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data["status"] != "REQUEST_SUCCEEDED":
        raise ValueError(f"BLS API error: {data.get('message', 'Unknown error')}")

    results = {}
    for series in data["Results"]["series"]:
        sid = series["seriesID"]
        rows = []
        for obs in series["data"]:
            if obs["period"] == "M13":   # M13 = annual average, skip
                continue
            rows.append({
                "year":   int(obs["year"]),
                "month":  int(obs["period"].replace("M", "")),
                "value":  float(obs["value"]) if obs["value"] != "-" else None,
                "period_name": obs["periodName"],
            })
        df = pd.DataFrame(rows).sort_values(["year","month"]).reset_index(drop=True)
        df["date"] = pd.to_datetime(df[["year","month"]].assign(day=1))
        results[sid] = df
        print(f"    ✓ {sid}: {len(df)} monthly observations")

    return results


def build_master_dataset(raw: dict) -> pd.DataFrame:
    """Combine all series into one analysis-ready DataFrame."""

    # ── 1. Total JOLTS measures ───────────────────────────────────────────
    measures = {
        "quits_rate":    "JTS000000000000000QUR",
        "openings_rate": "JTS000000000000000JOR",
        "hires_rate":    "JTS000000000000000HIR",
        "layoffs_rate":  "JTS000000000000000LDR",
    }

    base = None
    for col, sid in measures.items():
        if sid not in raw:
            continue
        df = raw[sid][["date","year","month","value"]].rename(columns={"value": col})
        base = df if base is None else base.merge(df, on=["date","year","month"], how="outer")

    # ── 2. Industry quits rates ───────────────────────────────────────────
    industry_series = {
        "accommodation":  "JTS7200000000000QUR",
        "retail":         "JTS4400000000000QUR",
        "healthcare":     "JTS6200000000000QUR",
        "finance":        "JTS5200000000000QUR",
        "manufacturing":  "JTS3000000000000QUR",
        "professional":   "JTS5400000000000QUR",
        "construction":   "JTS2300000000000QUR",
        "government":     "JTS9000000000000QUR",
    }

    for ind, sid in industry_series.items():
        if sid not in raw:
            continue
        col = f"quits_{ind}"
        df  = raw[sid][["date","value"]].rename(columns={"value": col})
        base = base.merge(df, on="date", how="left")

    base = base.sort_values("date").reset_index(drop=True)
    base["period"] = base["date"].dt.strftime("%Y-%m")

    # ── 3. Add derived columns ────────────────────────────────────────────
    # Great Resignation flag: Dec 2020 – Dec 2022
    base["great_resignation"] = (
        (base["date"] >= "2020-12-01") &
        (base["date"] <= "2022-12-01")
    ).astype(int)

    # Pre-pandemic baseline: Jan 2019 – Feb 2020
    base["pre_pandemic"] = (
        (base["date"] >= "2019-01-01") &
        (base["date"] <= "2020-02-01")
    ).astype(int)

    return base


def fetch_all(output_dir: str = "data/raw") -> pd.DataFrame:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Fetch in two batches (API limit: 25 series per call)
    batch1 = list(SERIES.values())[:13]
    batch2 = list(SERIES.values())[13:]

    raw = {}
    raw.update(fetch_series(batch1, "2019", "2024"))
    if batch2:
        time.sleep(2)
        raw.update(fetch_series(batch2, "2019", "2024"))

    # Save raw JSONs
    for sid, df in raw.items():
        df.to_csv(f"{output_dir}/{sid}.csv", index=False)

    master = build_master_dataset(raw)
    master.to_csv(f"{output_dir}/jolts_master.csv", index=False)
    print(f"\n  ✓ Master dataset: {len(master)} rows × {master.shape[1]} cols")
    return master
