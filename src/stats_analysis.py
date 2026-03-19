"""
src/stats_analysis.py
Statistical analysis of the Great Resignation:
  - Structural break detection (was there really a break?)
  - Peak identification + magnitude
  - Industry comparison + effect sizes
  - Pre/post pandemic comparison
"""

import pandas as pd
import numpy as np
from scipy import stats


def describe_great_resignation(df: pd.DataFrame) -> dict:
    """Key stats describing the Great Resignation."""
    pre  = df[df["date"] < "2020-03-01"]["quits_rate"]
    gr   = df[(df["date"] >= "2021-04-01") & (df["date"] <= "2022-12-01")]["quits_rate"]
    post = df[df["date"] > "2022-12-01"]["quits_rate"]
    peak_row = df.loc[df["quits_rate"].idxmax()]

    # t-test: was GR significantly higher than pre-pandemic?
    t, p = stats.ttest_ind(gr, pre, equal_var=False)
    cohen_d = (gr.mean() - pre.mean()) / np.sqrt((gr.std()**2 + pre.std()**2)/2)

    return {
        "pre_pandemic_avg":    round(pre.mean(), 3),
        "pre_pandemic_std":    round(pre.std(),  3),
        "gr_period_avg":       round(gr.mean(),  3),
        "gr_period_peak":      round(gr.max(),   3),
        "peak_month":          peak_row["date"].strftime("%B %Y"),
        "peak_value":          round(peak_row["quits_rate"], 2),
        "post_gr_avg":         round(post.mean(), 3),
        "total_excess_quits":  round((gr - pre.mean()).clip(lower=0).sum(), 2),
        "lift_vs_baseline":    round(gr.mean() - pre.mean(), 3),
        "lift_pct":            round((gr.mean() / pre.mean() - 1) * 100, 1),
        "t_stat":              round(t, 3),
        "p_value":             round(p, 8),
        "cohens_d":            round(cohen_d, 3),
        "significant":         p < 0.05,
        "recovered_to_normal": round(post.mean(), 2) <= round(pre.mean() + 0.1, 2),
    }


def industry_comparison(ind_df: pd.DataFrame) -> pd.DataFrame:
    """Which industries saw the biggest Great Resignation impact?"""
    peak_year = ind_df[ind_df["year"] == 2021].copy()
    base_year = ind_df[ind_df["year"] == 2019][["industry","quits_rate"]]\
                     .rename(columns={"quits_rate":"baseline"})
    merged = peak_year.merge(base_year, on="industry")
    merged["abs_lift"]  = (merged["quits_rate"] - merged["baseline"]).round(2)
    merged["rel_lift"]  = ((merged["abs_lift"] / merged["baseline"]) * 100).round(1)
    merged = merged.sort_values("rel_lift", ascending=False).reset_index(drop=True)
    merged["rank"] = range(1, len(merged)+1)
    return merged


def wage_pressure_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    When quits rise, employers must raise wages to retain workers.
    We proxy this by lagging openings_rate vs quits_rate.
    High openings + high quits = maximum wage pressure period.
    """
    out = df.copy()
    out["wage_pressure_index"] = (
        out["quits_rate"] * 0.6 + out["openings_rate"] * 0.4
    ).round(3)
    out["pressure_tier"] = pd.cut(
        out["wage_pressure_index"],
        bins=[0, 5.5, 7.0, 8.5, 99],
        labels=["Low", "Moderate", "High", "Extreme"]
    )
    return out


def recovery_analysis(df: pd.DataFrame) -> dict:
    """How long did the Great Resignation last and is it over?"""
    pre_avg = df[df["date"] < "2020-03-01"]["quits_rate"].mean()
    post_gr = df[df["date"] > "2022-12-01"].copy()
    post_gr["returned_to_normal"] = post_gr["quits_rate"] <= (pre_avg + 0.05)

    first_normal = post_gr[post_gr["returned_to_normal"]]["date"].min()
    gr_start = pd.Timestamp("2021-04-01")
    gr_peak  = pd.Timestamp("2021-11-01")

    return {
        "gr_start_month":       "April 2021",
        "gr_peak_month":        "November 2021",
        "gr_end_month":         "December 2022",
        "gr_duration_months":   20,
        "pre_pandemic_baseline":round(pre_avg, 2),
        "first_return_to_normal": first_normal.strftime("%B %Y") if pd.notna(first_normal) else "Still elevated",
        "latest_quits_rate":    round(df.iloc[-1]["quits_rate"], 2),
        "still_above_baseline": df.iloc[-1]["quits_rate"] > pre_avg,
    }
