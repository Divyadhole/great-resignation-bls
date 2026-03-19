"""
src/build_website.py
Standard module included in EVERY project.
Builds a self-contained docs/index.html with:
  - Project overview
  - Key findings
  - Embedded charts (base64)
  - Links to GitHub repo
  - Live data source links

Run: python src/build_website.py
Then: Settings → Pages → main → /docs → Save
Live at: https://divyadhole.github.io/{repo-name}/
"""

import base64
import json
import os
from pathlib import Path


def img_to_b64(path: str) -> str:
    """Convert image to base64 string for embedding in HTML."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""


def build(
    project_title: str,
    project_subtitle: str,
    repo_name: str,
    github_user: str,
    data_source: str,
    data_source_url: str,
    key_findings: list,       # list of {"label": str, "value": str, "color": str}
    chart_paths: list,        # list of {"path": str, "title": str, "subtitle": str}
    summary_text: str,
    project_number: int,
    tools: list,              # e.g. ["Python", "SQL", "BLS API"]
    output_dir: str = "docs",
):
    """Build the project website and save to docs/index.html."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Embed charts as base64
    chart_html = ""
    for chart in chart_paths:
        b64 = img_to_b64(chart["path"])
        if b64:
            chart_html += f"""
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">{chart['title']}</div>
                    <div class="chart-sub">{chart.get('subtitle','')}</div>
                </div>
                <img src="data:image/png;base64,{b64}" alt="{chart['title']}" loading="lazy">
            </div>"""

    # KPI cards
    kpi_html = ""
    for f in key_findings:
        kpi_html += f"""
            <div class="kpi" style="border-top: 3px solid {f.get('color','#2dd4a0')}">
                <div class="kpi-label">{f['label']}</div>
                <div class="kpi-value" style="color:{f.get('color','#2dd4a0')}">{f['value']}</div>
            </div>"""

    # Tool badges
    tool_html = " ".join([f'<span class="tool-badge">{t}</span>' for t in tools])

    github_url = f"https://github.com/{github_user}/{repo_name}"
    pages_url  = f"https://{github_user.lower()}.github.io/{repo_name}/"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
  :root {{
    --bg:#0f1117;--surface:#1a1d27;--card:#20232f;--border:#2e3244;
    --text:#e8eaf0;--muted:#6b7280;--teal:#2dd4a0;--red:#f87171;
    --amber:#fbbf24;--blue:#60a5fa;--purple:#a78bfa;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);font-size:15px;line-height:1.6}}

  /* ── Header ── */
  .header{{background:var(--surface);border-bottom:1px solid var(--border);padding:0 32px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}}
  .header-left{{display:flex;align-items:center;gap:14px}}
  .proj-num{{width:36px;height:36px;background:var(--teal);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#0f1117}}
  .header h1{{font-size:16px;font-weight:600}}
  .header h1 span{{color:var(--muted);font-weight:400;font-size:13px;margin-left:8px}}
  .header-links{{display:flex;gap:10px}}
  .btn{{padding:6px 16px;border-radius:6px;font-size:12px;font-weight:500;cursor:pointer;text-decoration:none;font-family:inherit;transition:all .15s}}
  .btn-ghost{{background:transparent;border:1px solid var(--border);color:var(--muted)}}
  .btn-ghost:hover{{border-color:var(--teal);color:var(--teal)}}
  .btn-primary{{background:var(--teal);border:none;color:#0f1117}}
  .btn-primary:hover{{opacity:.88}}

  /* ── Hero ── */
  .hero{{background:linear-gradient(135deg,#0a2e22 0%,#0f1117 60%);padding:52px 32px 44px;border-bottom:1px solid var(--border)}}
  .hero-inner{{max-width:960px;margin:0 auto}}
  .source-badge{{display:inline-flex;align-items:center;gap:6px;font-size:11px;background:rgba(45,212,160,.12);color:var(--teal);border:1px solid rgba(45,212,160,.3);padding:4px 12px;border-radius:99px;margin-bottom:16px;font-weight:500}}
  .hero h2{{font-size:2.2rem;font-weight:700;line-height:1.2;margin-bottom:10px;color:var(--text)}}
  .hero p{{font-size:1.05rem;color:var(--muted);max-width:680px;margin-bottom:20px}}
  .tools{{display:flex;gap:8px;flex-wrap:wrap}}
  .tool-badge{{font-size:11px;padding:3px 10px;border-radius:99px;background:var(--card);border:1px solid var(--border);color:var(--muted);font-weight:500}}

  /* ── Container ── */
  .container{{max-width:960px;margin:0 auto;padding:36px 32px}}

  /* ── Finding box ── */
  .finding-box{{background:rgba(45,212,160,.08);border:1px solid rgba(45,212,160,.2);border-left:4px solid var(--teal);border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:32px;font-size:13.5px;color:#a7f3d0;line-height:1.7}}
  .finding-box strong{{color:var(--teal)}}

  /* ── KPI grid ── */
  .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:36px}}
  .kpi{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 20px}}
  .kpi-label{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:500;margin-bottom:8px}}
  .kpi-value{{font-size:1.9rem;font-weight:700;font-family:'DM Mono',monospace;line-height:1.1}}

  /* ── Section headers ── */
  .section-title{{font-size:1.1rem;font-weight:600;color:var(--text);margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid var(--border)}}

  /* ── Charts ── */
  .charts-grid{{display:grid;grid-template-columns:1fr;gap:20px;margin-bottom:36px}}
  .chart-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden}}
  .chart-header{{padding:16px 20px 0}}
  .chart-title{{font-size:13px;font-weight:600;color:var(--text);margin-bottom:2px}}
  .chart-sub{{font-size:11px;color:var(--muted);margin-bottom:12px}}
  .chart-card img{{width:100%;display:block}}

  /* ── Source section ── */
  .source-section{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px 24px;margin-bottom:24px}}
  .source-section h3{{font-size:13px;font-weight:600;color:var(--text);margin-bottom:10px}}
  .source-section p{{font-size:12.5px;color:var(--muted);line-height:1.65}}
  .source-section a{{color:var(--teal);text-decoration:none}}
  .source-section a:hover{{text-decoration:underline}}

  /* ── Footer ── */
  footer{{text-align:center;padding:24px;font-size:11.5px;color:var(--muted);border-top:1px solid var(--border)}}
  footer a{{color:var(--teal);text-decoration:none}}

  ::-webkit-scrollbar{{width:5px}}
  ::-webkit-scrollbar-track{{background:var(--bg)}}
  ::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}
</style>
</head>
<body>

<header class="header">
  <div class="header-left">
    <div class="proj-num">P{project_number}</div>
    <h1>{project_title} <span>{project_subtitle}</span></h1>
  </div>
  <div class="header-links">
    <a href="{github_url}" target="_blank" class="btn btn-ghost">GitHub Repo</a>
    <a href="{data_source_url}" target="_blank" class="btn btn-ghost">Data Source</a>
  </div>
</header>

<div class="hero">
  <div class="hero-inner">
    <div class="source-badge">Real Government Data — {data_source}</div>
    <h2>{project_title}</h2>
    <p>{summary_text}</p>
    <div class="tools">{tool_html}</div>
  </div>
</div>

<div class="container">

  <div class="finding-box">
    <strong>Project Summary:</strong> {summary_text}
  </div>

  <div class="section-title">Key Findings</div>
  <div class="kpi-grid">{kpi_html}</div>

  <div class="section-title">Charts & Analysis</div>
  <div class="charts-grid">{chart_html}</div>

  <div class="source-section">
    <h3>Data Source</h3>
    <p>
      <strong>{data_source}</strong> — <a href="{data_source_url}" target="_blank">{data_source_url}</a><br>
      All data used in this project is real, publicly available government data. Free to download and verify.
    </p>
  </div>

</div>

<footer>
  <a href="{github_url}" target="_blank">GitHub</a> &nbsp;|&nbsp;
  Data: <a href="{data_source_url}" target="_blank">{data_source}</a> (public domain) &nbsp;|&nbsp;
  Junior Data Analyst Portfolio — Divyadhole &nbsp;|&nbsp; Project {project_number} of 40
</footer>

</body>
</html>"""

    out_path = f"{output_dir}/index.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"  ✓ Website built → {out_path}")
    print(f"  ✓ Push to GitHub then enable Pages:")
    print(f"    Settings → Pages → main → /docs → Save")
    print(f"  ✓ Live at: {pages_url}")
    return out_path


if __name__ == "__main__":
    # Example — run from project root to rebuild this project's site
    build(
        project_title    = "The Great Resignation",
        project_subtitle = "BLS JOLTS Labor Market Analysis",
        repo_name        = "great-resignation-bls",
        github_user      = "Divyadhole",
        data_source      = "US Bureau of Labor Statistics — JOLTS",
        data_source_url  = "https://www.bls.gov/jlt/",
        key_findings     = [
            {"label":"Pre-pandemic quit rate",  "value":"2.3%",  "color":"#60a5fa"},
            {"label":"GR peak quit rate",       "value":"3.0%",  "color":"#f87171"},
            {"label":"Lift vs baseline",        "value":"+19.7%","color":"#fbbf24"},
            {"label":"Effect size (Cohen's d)", "value":"3.82",  "color":"#a78bfa"},
            {"label":"GR duration",             "value":"20 mo", "color":"#fbbf24"},
            {"label":"Latest quit rate",        "value":"2.2%",  "color":"#2dd4a0"},
        ],
        chart_paths = [
            {"path":"outputs/charts/01_quit_rate_timeline.png",    "title":"US Monthly Quit Rate 2019–2023", "subtitle":"Seasonally adjusted — BLS JOLTS"},
            {"path":"outputs/charts/02_all_jolts_measures.png",    "title":"All JOLTS Measures",             "subtitle":"Quits · Openings · Hires · Layoffs"},
            {"path":"outputs/charts/03_industry_comparison.png",   "title":"Industry Comparison",           "subtitle":"Which industries saw the biggest walkout?"},
            {"path":"outputs/charts/04_industry_heatmap.png",      "title":"Industry Heatmap",              "subtitle":"Quit rate by industry and year"},
            {"path":"outputs/charts/05_quits_vs_openings.png",     "title":"Wage Pressure Map",             "subtitle":"Quits vs Job Openings — each dot = one month"},
            {"path":"outputs/charts/06_recovery_trajectory.png",   "title":"Is the Great Resignation Over?","subtitle":"Tracking recovery to pre-pandemic normal"},
        ],
        summary_text  = (
            "Was the Great Resignation real? Using real monthly data from the US Bureau of "
            "Labor Statistics JOLTS survey, this project proves it was — and quantifies exactly "
            "how big it was. The quit rate peaked at 3.0% in November 2021, +19.7% above the "
            "pre-pandemic baseline. Welch t-test: p < 0.001, Cohen's d = 3.82 (large effect). "
            "The Great Resignation lasted 20 months and returned to normal by July 2023."
        ),
        project_number = 5,
        tools = ["Python", "SQL", "BLS JOLTS API", "scipy", "matplotlib", "SQLite", "Chart.js"],
    )
