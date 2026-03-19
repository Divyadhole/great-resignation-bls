"""
src/charts.py — Great Resignation investigative charts
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
from pathlib import Path

P = {"red":"#A32D2D","teal":"#1D9E75","blue":"#185FA5","amber":"#BA7517",
     "purple":"#534AB7","coral":"#D85A30","neutral":"#5F5E5A",
     "light":"#F1EFE8","mid":"#B4B2A9","dark":"#2C2C2A"}

BASE = {"figure.facecolor":"white","axes.facecolor":"#FAFAF8",
        "axes.spines.top":False,"axes.spines.right":False,"axes.spines.left":False,
        "axes.grid":True,"axes.grid.axis":"y","grid.color":"#ECEAE4","grid.linewidth":0.6,
        "font.family":"DejaVu Sans","axes.titlesize":12,"axes.titleweight":"bold",
        "axes.labelsize":10,"xtick.labelsize":8.5,"ytick.labelsize":9,
        "xtick.bottom":False,"ytick.left":False}

def save(fig, path):
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  ✓ {Path(path).name}")


def chart_quit_rate_timeline(df: pd.DataFrame, stats: dict, path: str):
    """The headline chart — quits rate 2019–2023 with annotations."""
    pre_avg = stats["pre_pandemic_avg"]

    with plt.rc_context({**BASE,"axes.grid.axis":"both","grid.alpha":0.5}):
        fig, ax = plt.subplots(figsize=(14, 6))

        # Shade Great Resignation period
        gr_start = pd.Timestamp("2021-04-01")
        gr_end   = pd.Timestamp("2022-12-01")
        ax.axvspan(gr_start, gr_end, alpha=0.08, color=P["amber"], label="Great Resignation period")

        # Shade pandemic crash
        ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2020-06-01"),
                   alpha=0.1, color=P["red"], label="COVID-19 shutdown")

        # Pre-pandemic baseline
        ax.axhline(pre_avg, color=P["neutral"], linestyle="--", lw=1.3,
                   label=f"Pre-pandemic avg: {pre_avg}%", zorder=2)

        # Main line
        ax.plot(df["date"], df["quits_rate"],
                color=P["blue"], lw=2.2, zorder=3)
        ax.fill_between(df["date"], pre_avg, df["quits_rate"],
                        where=df["quits_rate"] > pre_avg,
                        alpha=0.15, color=P["amber"])
        ax.fill_between(df["date"], pre_avg, df["quits_rate"],
                        where=df["quits_rate"] < pre_avg,
                        alpha=0.15, color=P["red"])

        # Annotate peak
        peak_date = df.loc[df["quits_rate"].idxmax(), "date"]
        peak_val  = df["quits_rate"].max()
        ax.annotate(
            f"PEAK: {peak_val}%\n{stats['peak_month']}",
            xy=(peak_date, peak_val),
            xytext=(peak_date + pd.DateOffset(months=3), peak_val + 0.15),
            fontsize=9, fontweight="bold", color=P["red"],
            arrowprops=dict(arrowstyle="->", color=P["red"], lw=1.2)
        )

        # Key events
        events = [
            ("2020-03-01", "COVID\nshutdown",   P["red"],    -0.45),
            ("2021-03-01", "Stimulus\nchecks",  P["teal"],    0.20),
            ("2022-03-01", "Fed raises\nrates",  P["purple"], 0.20),
        ]
        for date_str, label, color, yoff in events:
            xdt = pd.Timestamp(date_str)
            yval = df.loc[df["date"].sub(xdt).abs().idxmin(), "quits_rate"]
            ax.annotate(label, xy=(xdt, yval), xytext=(xdt, yval + yoff),
                        fontsize=7.5, ha="center", color=color,
                        arrowprops=dict(arrowstyle="-", color=color, lw=0.8))

        ax.set_ylabel("Quits Rate (% of total employment)")
        ax.set_xlabel("")
        ax.set_ylim(0.5, 3.7)
        ax.set_title(
            "The Great Resignation — US Monthly Quit Rate 2019–2023\n"
            f"Peak: {peak_val}% ({stats['peak_month']}) vs pre-pandemic avg {pre_avg}%  "
            f"|  Lift: +{stats['lift_pct']}%  |  Welch t-test p < 0.001",
            fontsize=11
        )
        ax.legend(fontsize=8.5, loc="upper left")
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        fig.tight_layout()
        save(fig, path)


def chart_all_jolts_measures(df: pd.DataFrame, path: str):
    """4-panel: Quits, Openings, Hires, Layoffs on one figure."""
    measures = [
        ("quits_rate",    "Quits Rate (%)",    P["amber"],  "Workers voluntarily leaving"),
        ("openings_rate", "Job Openings (%)",  P["teal"],   "Unfilled positions per 100 workers"),
        ("hires_rate",    "Hires Rate (%)",    P["blue"],   "New hires per 100 workers"),
        ("layoffs_rate",  "Layoffs Rate (%)",  P["red"],    "Involuntary separations"),
    ]

    with plt.rc_context({**BASE,"axes.grid.axis":"both"}):
        fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True)
        axes = axes.flatten()

        for ax, (col, ylabel, color, desc) in zip(axes, measures):
            gr_s = pd.Timestamp("2021-04-01")
            gr_e = pd.Timestamp("2022-12-01")
            ax.axvspan(gr_s, gr_e, alpha=0.07, color=P["amber"])
            ax.plot(df["date"], df[col], color=color, lw=2)
            ax.fill_between(df["date"], df[col].min()*0.95, df[col],
                            alpha=0.12, color=color)
            ax.set_ylabel(ylabel)
            ax.set_title(desc, fontsize=9.5, fontweight="bold")
            ax.spines["left"].set_visible(True)
            ax.spines["bottom"].set_visible(True)

            # Mark peak
            pidx = df[col].idxmax()
            ax.scatter(df.loc[pidx,"date"], df.loc[pidx,col],
                       color=color, s=60, zorder=5)

        gr_patch = mpatches.Patch(color=P["amber"], alpha=0.3, label="Great Resignation period")
        fig.legend(handles=[gr_patch], fontsize=9, loc="lower center", ncol=1)
        fig.suptitle("JOLTS Four Measures — Full Labor Market Picture 2019–2023",
                     fontsize=13, fontweight="bold", y=1.01)
        fig.tight_layout()
        save(fig, path)


def chart_industry_comparison(ind_df: pd.DataFrame, path: str):
    """Which industries had the biggest quits surge?"""
    years = [2019, 2021, 2022, 2023]
    pivot = ind_df[ind_df["year"].isin(years)].pivot(
        index="industry", columns="year", values="quits_rate"
    )
    pivot = pivot.sort_values(2021, ascending=True)

    with plt.rc_context(BASE):
        fig, ax = plt.subplots(figsize=(12, 6))
        y  = np.arange(len(pivot))
        h  = 0.18
        colors = {2019:P["mid"], 2021:P["red"], 2022:P["amber"], 2023:P["teal"]}

        for i, (yr, color) in enumerate(colors.items()):
            if yr in pivot.columns:
                bars = ax.barh(y + (i-1.5)*h, pivot[yr], height=h,
                               color=color, alpha=0.85, label=str(yr))

        ax.set_yticks(y)
        ax.set_yticklabels(pivot.index, fontsize=9)
        ax.set_xlabel("Annual Avg Quits Rate (% of employment)")
        ax.set_title("Great Resignation by Industry — Quits Rate 2019 vs 2021 vs 2022 vs 2023\n"
                     "Accommodation & Food Services led the walkout")
        ax.legend(title="Year", fontsize=9)
        ax.axvline(0, color=P["dark"], lw=0.5)
        fig.tight_layout()
        save(fig, path)


def chart_industry_lift_heatmap(ind_df: pd.DataFrame, path: str):
    """Heatmap: industry × year quits rate."""
    import seaborn as sns
    pivot = ind_df.pivot(index="industry", columns="year", values="quits_rate")
    pivot = pivot.sort_values(2021, ascending=False)

    with plt.rc_context({**BASE,"axes.grid":False}):
        fig, ax = plt.subplots(figsize=(10, 5.5))
        sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd",
                    linewidths=0.5, linecolor="#E0DED8",
                    cbar_kws={"label":"Quits Rate (%)"}, ax=ax)
        ax.set_title("Quits Rate Heatmap — Industry × Year\n"
                     "Darker = more workers quitting", fontweight="bold")
        ax.set_ylabel("")
        plt.xticks(rotation=0)
        plt.yticks(rotation=0)
        fig.tight_layout()
        save(fig, path)


def chart_quit_vs_openings(df: pd.DataFrame, path: str):
    """Scatter: quits rate vs openings rate — the wage pressure picture."""
    with plt.rc_context({**BASE,"axes.grid":False}):
        fig, ax = plt.subplots(figsize=(10, 6))

        # Color by period
        period_colors = []
        for _, row in df.iterrows():
            if row["date"] < pd.Timestamp("2020-03-01"):
                period_colors.append(P["blue"])
            elif row["date"] < pd.Timestamp("2021-04-01"):
                period_colors.append(P["red"])
            elif row["date"] <= pd.Timestamp("2022-12-01"):
                period_colors.append(P["amber"])
            else:
                period_colors.append(P["teal"])

        sc = ax.scatter(df["openings_rate"], df["quits_rate"],
                        c=period_colors, s=55, alpha=0.8,
                        edgecolors="white", linewidths=0.6, zorder=3)

        # Trend line
        z = np.polyfit(df["openings_rate"].dropna(), df["quits_rate"].dropna(), 1)
        xr = np.linspace(df["openings_rate"].min(), df["openings_rate"].max(), 100)
        ax.plot(xr, np.poly1d(z)(xr), "--", color=P["neutral"], lw=1.2, alpha=0.7,
                label=f"Trend (r²={np.corrcoef(df['openings_rate'],df['quits_rate'])[0,1]**2:.2f})")

        # Annotate peak point
        pidx = df["quits_rate"].idxmax()
        ax.annotate("Nov 2021\n(GR Peak)",
                    xy=(df.loc[pidx,"openings_rate"], df.loc[pidx,"quits_rate"]),
                    xytext=(9.5, 2.8), fontsize=8, color=P["red"],
                    arrowprops=dict(arrowstyle="->", color=P["red"], lw=1))

        patches = [
            mpatches.Patch(color=P["blue"],  label="Pre-pandemic (2019–Feb 2020)"),
            mpatches.Patch(color=P["red"],   label="COVID shock (Mar–Dec 2020)"),
            mpatches.Patch(color=P["amber"], label="Great Resignation (2021–2022)"),
            mpatches.Patch(color=P["teal"],  label="Post-GR recovery (2023)"),
        ]
        ax.legend(handles=patches, fontsize=8.5, loc="lower right")
        ax.set_xlabel("Job Openings Rate (% of employment)")
        ax.set_ylabel("Quits Rate (% of employment)")
        ax.set_title("Quits vs Openings — The Great Resignation Wage Pressure Map\n"
                     "More openings + more quits = employers desperate for workers = wages must rise")
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        fig.tight_layout()
        save(fig, path)


def chart_recovery_trajectory(df: pd.DataFrame, stats: dict, path: str):
    """Is the Great Resignation truly over?"""
    pre_avg = stats["pre_pandemic_avg"]
    post    = df[df["date"] >= "2022-06-01"].copy()

    with plt.rc_context({**BASE,"axes.grid.axis":"both"}):
        fig, ax = plt.subplots(figsize=(11, 5))

        ax.axhline(pre_avg, color=P["neutral"], linestyle="--", lw=1.3,
                   label=f"Pre-pandemic normal: {pre_avg}%", alpha=0.8)
        ax.axhspan(pre_avg - 0.05, pre_avg + 0.05,
                   alpha=0.12, color=P["teal"], label="±0.05% of normal")

        ax.plot(post["date"], post["quits_rate"],
                "o-", color=P["blue"], lw=2, markersize=5)
        ax.fill_between(post["date"], pre_avg, post["quits_rate"],
                        where=post["quits_rate"] > pre_avg,
                        alpha=0.2, color=P["amber"],
                        label="Still above normal")

        latest = post.iloc[-1]
        ax.annotate(f"Latest: {latest['quits_rate']}%\n({latest['date'].strftime('%b %Y')})",
                    xy=(latest["date"], latest["quits_rate"]),
                    xytext=(latest["date"] - pd.DateOffset(months=5),
                            latest["quits_rate"] + 0.12),
                    fontsize=9, color=P["blue"],
                    arrowprops=dict(arrowstyle="->", color=P["blue"], lw=1))

        ax.set_ylabel("Quits Rate (%)")
        ax.set_title("Is the Great Resignation Over?\n"
                     "Tracking the recovery back to pre-pandemic quit rates")
        ax.legend(fontsize=9)
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        fig.tight_layout()
        save(fig, path)
