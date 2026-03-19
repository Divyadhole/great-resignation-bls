"""
run_analysis.py — Great Resignation BLS JOLTS Analysis
Real data from the US Bureau of Labor Statistics.
"""

import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from src.bls_data       import load_total_jolts, load_industry_quits
from src.stats_analysis import (describe_great_resignation,
                                 industry_comparison, recovery_analysis,
                                 wage_pressure_proxy)
from src.charts import (chart_quit_rate_timeline, chart_all_jolts_measures,
                         chart_industry_comparison, chart_industry_lift_heatmap,
                         chart_quit_vs_openings, chart_recovery_trajectory)

CHARTS = "outputs/charts"
EXCEL  = "outputs/excel"
DB     = "data/jolts.db"

os.makedirs(CHARTS, exist_ok=True)
os.makedirs(EXCEL,  exist_ok=True)
os.makedirs("data/raw", exist_ok=True)

print("=" * 62)
print("  THE GREAT RESIGNATION — BLS JOLTS ANALYSIS")
print("  Source: US Bureau of Labor Statistics (public data)")
print("=" * 62)

# ── 1. Load real BLS data ─────────────────────────────────────
print("\n[1/5] Loading BLS JOLTS data...")
df_total = load_total_jolts()
df_ind   = load_industry_quits()
df_total = wage_pressure_proxy(df_total)

print(f"  ✓ Total JOLTS: {len(df_total)} monthly observations (Jan 2019–Dec 2023)")
print(f"  ✓ Industry data: {len(df_ind)} rows × {df_ind['industry'].nunique()} industries")
print(f"  ✓ Date range: {df_total['date'].min().strftime('%b %Y')} – "
      f"{df_total['date'].max().strftime('%b %Y')}")

# ── 2. Load to SQLite ─────────────────────────────────────────
print("\n[2/5] Loading to SQLite...")
conn = sqlite3.connect(DB)
df_total.to_sql("jolts_total",    conn, if_exists="replace", index=False)
df_ind.to_sql("industry_quits",   conn, if_exists="replace", index=False)
conn.close()
print(f"  ✓ DB → {DB}")

# ── 3. Statistical analysis ───────────────────────────────────
print("\n[3/5] Statistical analysis...")
stats   = describe_great_resignation(df_total)
ind_cmp = industry_comparison(df_ind)
recovery = recovery_analysis(df_total)

print(f"\n  PRE-PANDEMIC BASELINE (2019–Feb 2020)")
print(f"    Avg quit rate:     {stats['pre_pandemic_avg']}%")
print(f"\n  GREAT RESIGNATION (Apr 2021–Dec 2022)")
print(f"    Avg quit rate:     {stats['gr_period_avg']}%")
print(f"    Peak quit rate:    {stats['peak_value']}%  ({stats['peak_month']})")
print(f"    Lift vs baseline:  +{stats['lift_vs_baseline']}pp  (+{stats['lift_pct']}%)")
print(f"    Statistical test:  Welch t={stats['t_stat']},  p={stats['p_value']:.2e}")
print(f"    Effect size:       Cohen's d = {stats['cohens_d']}  (large)")
print(f"\n  RECOVERY (2023)")
print(f"    Latest quit rate:  {recovery['latest_quits_rate']}%")
print(f"    Returned to normal:{recovery['first_return_to_normal']}")
print(f"\n  TOP INDUSTRIES BY GR IMPACT:")
for _, row in ind_cmp.head(4).iterrows():
    print(f"    {row['rank']}. {row['industry']:<38} +{row['rel_lift']}%")

# ── 4. Charts ─────────────────────────────────────────────────
print("\n[4/5] Generating charts...")
chart_quit_rate_timeline  (df_total, stats, f"{CHARTS}/01_quit_rate_timeline.png")
chart_all_jolts_measures  (df_total,        f"{CHARTS}/02_all_jolts_measures.png")
chart_industry_comparison (df_ind,          f"{CHARTS}/03_industry_comparison.png")
chart_industry_lift_heatmap(df_ind,         f"{CHARTS}/04_industry_heatmap.png")
chart_quit_vs_openings    (df_total,        f"{CHARTS}/05_quits_vs_openings.png")
chart_recovery_trajectory (df_total, stats, f"{CHARTS}/06_recovery_trajectory.png")

# ── 5. Excel workbook ─────────────────────────────────────────
print("\n[5/5] Building Excel workbook...")
conn = sqlite3.connect(DB)

sheets = {
    "Key Findings": pd.DataFrame([
        {"Metric": "Pre-pandemic avg quit rate",      "Value": f"{stats['pre_pandemic_avg']}%"},
        {"Metric": "Great Resignation avg quit rate", "Value": f"{stats['gr_period_avg']}%"},
        {"Metric": "Peak quit rate",                  "Value": f"{stats['peak_value']}% ({stats['peak_month']})"},
        {"Metric": "Lift vs pre-pandemic",            "Value": f"+{stats['lift_pct']}%"},
        {"Metric": "Statistical significance",        "Value": f"p = {stats['p_value']:.2e}"},
        {"Metric": "Effect size (Cohen's d)",         "Value": str(stats["cohens_d"])},
        {"Metric": "GR duration",                     "Value": f"{recovery['gr_duration_months']} months"},
        {"Metric": "Latest quit rate (Dec 2023)",     "Value": f"{recovery['latest_quits_rate']}%"},
    ]),
    "Monthly JOLTS": df_total[["date","year","month","quits_rate","openings_rate",
                                "hires_rate","layoffs_rate","wage_pressure_index",
                                "pressure_tier","above_prepandemic"]].copy(),
    "Industry Quits": df_ind,
    "Industry GR Impact": ind_cmp.sort_values("rel_lift", ascending=False),
    "Phase Comparison": pd.read_sql("""
        SELECT
            CASE
                WHEN date < '2020-03-01' THEN '1. Pre-pandemic'
                WHEN date BETWEEN '2020-03-01' AND '2020-11-30' THEN '2. COVID shock'
                WHEN date BETWEEN '2020-12-01' AND '2021-03-31' THEN '3. Transition'
                WHEN date BETWEEN '2021-04-01' AND '2022-12-31' THEN '4. Great Resignation'
                ELSE '5. Recovery'
            END AS phase,
            COUNT(*) months,
            ROUND(AVG(quits_rate),3) avg_quits,
            ROUND(MAX(quits_rate),3) peak_quits,
            ROUND(AVG(openings_rate),3) avg_openings,
            ROUND(AVG(layoffs_rate),3) avg_layoffs
        FROM jolts_total GROUP BY phase ORDER BY phase
    """, conn),
    "Top Pressure Months": pd.read_sql("""
        SELECT date, quits_rate, openings_rate,
               ROUND(quits_rate*0.6+openings_rate*0.4,3) wage_pressure_index,
               CASE WHEN quits_rate*0.6+openings_rate*0.4>=8.5 THEN 'Extreme'
                    WHEN quits_rate*0.6+openings_rate*0.4>=7.0 THEN 'High'
                    WHEN quits_rate*0.6+openings_rate*0.4>=5.5 THEN 'Moderate'
                    ELSE 'Low' END pressure_tier
        FROM jolts_total ORDER BY wage_pressure_index DESC LIMIT 20
    """, conn),
}

excel_path = f"{EXCEL}/great_resignation_bls_analysis.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    for name, df in sheets.items():
        df.to_excel(writer, sheet_name=name, index=False)
        ws = writer.sheets[name]
        for col in ws.columns:
            w = max(len(str(c.value or "")) for c in col) + 3
            ws.column_dimensions[col[0].column_letter].width = min(w, 38)

conn.close()
print(f"  ✓ Excel → {excel_path}  ({len(sheets)} sheets)")

print("\n" + "=" * 62)
print("  PIPELINE COMPLETE")
print("=" * 62)
print(f"  Data source  : BLS JOLTS (US Bureau of Labor Statistics)")
print(f"  Date range   : Jan 2019 – Dec 2023  (60 months)")
print(f"  Key finding  : Quit rate peaked at {stats['peak_value']}% — "
      f"+{stats['lift_pct']}% above pre-pandemic")
print(f"  Charts       → {CHARTS}/  (6 files)")
print(f"  Excel        → {excel_path}")
