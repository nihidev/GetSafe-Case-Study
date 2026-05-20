import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUT = os.path.dirname(__file__)

PARTY_COLORS = {
    "berlinre":   "#1E40AF",
    "dronant":    "#065F46",
    "getland":    "#92400E",
    "liadigital": "#6B21A8",
}
STATUS_COLORS = {
    "processed": "#16A34A",
    "refunded":  "#F59E0B",
    "failed":    "#DC2626",
}
ACCOUNTING_COLOR = "#374151"
FINANCE_COLOR    = "#2563EB"

MONTHS       = ["2025-06", "2025-07", "2025-08"]
MONTH_LABELS = ["Jun 2025", "Jul 2025", "Aug 2025"]
PARTIES      = ["berlinre", "dronant", "getland", "liadigital"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 0.35,
    "figure.dpi": 150,
})

MONTHLY_PREMIUMS = {
    ("berlinre",   "2025-06"): (1476.45, 1127.42, 208),
    ("berlinre",   "2025-07"): (1084.40, 1024.93, 170),
    ("berlinre",   "2025-08"): (714.06,   705.18, 117),
    ("dronant",    "2025-06"): (2983.41, 2257.05, 424),
    ("dronant",    "2025-07"): (1771.90, 1661.43, 265),
    ("dronant",    "2025-08"): (1100.99, 1087.83, 183),
    ("getland",    "2025-06"): (1730.31, 1317.68, 240),
    ("getland",    "2025-07"): (1412.28, 1305.80, 176),
    ("getland",    "2025-08"): (660.19,   651.12,  95),
    ("liadigital", "2025-06"): (2239.33, 1723.61, 331),
    ("liadigital", "2025-07"): (1353.47, 1252.87, 221),
    ("liadigital", "2025-08"): (878.49,   867.06, 148),
}

ACCOUNTING = {
    ("berlinre",   "2025-06"): 1483.22,
    ("berlinre",   "2025-07"): 1098.74,
    ("berlinre",   "2025-08"): 714.06,
    ("dronant",    "2025-06"): 2983.41,
    ("dronant",    "2025-07"): 1780.19,
    ("dronant",    "2025-08"): 1107.07,
    ("getland",    "2025-06"): 1730.31,
    ("getland",    "2025-07"): 1412.28,
    ("getland",    "2025-08"): 660.19,
    ("liadigital", "2025-06"): 2241.79,
    ("liadigital", "2025-07"): 1353.47,
    ("liadigital", "2025-08"): 878.49,
}

TXN_SUMMARY = {
    ("berlinre",   "2025-06", "processed"): (208, 1476.45),
    ("berlinre",   "2025-06", "refunded"):  (5,   21.86),
    ("berlinre",   "2025-06", "failed"):    (4,   18.86),
    ("berlinre",   "2025-07", "processed"): (170, 1084.40),
    ("berlinre",   "2025-07", "refunded"):  (4,   27.85),
    ("berlinre",   "2025-07", "failed"):    (2,   9.98),
    ("berlinre",   "2025-08", "processed"): (117, 714.06),
    ("berlinre",   "2025-08", "refunded"):  (3,   54.13),
    ("berlinre",   "2025-08", "failed"):    (1,   4.76),
    ("dronant",    "2025-06", "processed"): (424, 2983.41),
    ("dronant",    "2025-06", "refunded"):  (9,   48.17),
    ("dronant",    "2025-06", "failed"):    (2,   14.82),
    ("dronant",    "2025-07", "processed"): (265, 1771.90),
    ("dronant",    "2025-07", "refunded"):  (3,   41.59),
    ("dronant",    "2025-07", "failed"):    (6,   22.64),
    ("dronant",    "2025-08", "processed"): (183, 1100.99),
    ("dronant",    "2025-08", "refunded"):  (1,   3.60),
    ("dronant",    "2025-08", "failed"):    (0,   0),
    ("getland",    "2025-06", "processed"): (240, 1730.31),
    ("getland",    "2025-06", "refunded"):  (6,   24.59),
    ("getland",    "2025-06", "failed"):    (1,   1.63),
    ("getland",    "2025-07", "processed"): (176, 1412.28),
    ("getland",    "2025-07", "refunded"):  (3,   13.12),
    ("getland",    "2025-07", "failed"):    (5,   65.71),
    ("getland",    "2025-08", "processed"): (95,  660.19),
    ("getland",    "2025-08", "refunded"):  (3,   19.69),
    ("getland",    "2025-08", "failed"):    (0,   0),
    ("liadigital", "2025-06", "processed"): (331, 2239.33),
    ("liadigital", "2025-06", "refunded"):  (6,   33.17),
    ("liadigital", "2025-06", "failed"):    (3,   9.35),
    ("liadigital", "2025-07", "processed"): (221, 1353.47),
    ("liadigital", "2025-07", "refunded"):  (3,   12.53),
    ("liadigital", "2025-07", "failed"):    (4,   21.11),
    ("liadigital", "2025-08", "processed"): (148, 878.49),
    ("liadigital", "2025-08", "refunded"):  (1,   2.16),
    ("liadigital", "2025-08", "failed"):    (1,   5.31),
}

RECON_STATUS = {
    ("berlinre",   "2025-06"): ("NEAR_MATCH",  -6.77),
    ("berlinre",   "2025-07"): ("DISCREPANCY", -14.34),
    ("berlinre",   "2025-08"): ("MATCH",         0.00),
    ("dronant",    "2025-06"): ("MATCH",          0.00),
    ("dronant",    "2025-07"): ("NEAR_MATCH",   -8.29),
    ("dronant",    "2025-08"): ("NEAR_MATCH",   -6.08),
    ("getland",    "2025-06"): ("MATCH",          0.00),
    ("getland",    "2025-07"): ("MATCH",          0.00),
    ("getland",    "2025-08"): ("MATCH",          0.00),
    ("liadigital", "2025-06"): ("NEAR_MATCH",   -2.46),
    ("liadigital", "2025-07"): ("MATCH",          0.00),
    ("liadigital", "2025-08"): ("MATCH",          0.00),
}


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {name}")


def chart_01_monthly_written_premium():
    fig, ax = plt.subplots(figsize=(11, 6))
    n_months, n_parties, bar_width = len(MONTHS), len(PARTIES), 0.18
    x = np.arange(n_months)

    for i, party in enumerate(PARTIES):
        vals = [MONTHLY_PREMIUMS.get((party, m), (0, 0, 0))[0] for m in MONTHS]
        offset = (i - (n_parties - 1) / 2) * bar_width
        bars = ax.bar(x + offset, vals, bar_width, label=party.capitalize(),
                      color=PARTY_COLORS[party], alpha=0.88, zorder=3)
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 25,
                        f"€{v:,.0f}", ha="center", va="bottom",
                        fontsize=7.5, fontweight="bold", color=PARTY_COLORS[party])

    ax.set_xticks(x)
    ax.set_xticklabels(MONTH_LABELS, fontsize=11)
    ax.set_ylabel("Written Premium (EUR)", fontsize=11)
    ax.set_title("Monthly Written Premium by Party  (status = processed)",
                 fontsize=13, fontweight="bold", pad=14)
    ax.legend(title="Party", fontsize=9, title_fontsize=9)
    ax.set_ylim(0, 3600)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"€{v:,.0f}"))
    fig.tight_layout()
    save(fig, "01_monthly_written_premium.png")


def chart_02_written_vs_earned():
    written = [sum(MONTHLY_PREMIUMS.get((p, m), (0, 0, 0))[0] for p in PARTIES) for m in MONTHS]
    earned  = [sum(MONTHLY_PREMIUMS.get((p, m), (0, 0, 0))[1] for p in PARTIES) for m in MONTHS]

    x, w = np.arange(len(MONTHS)), 0.35
    fig, ax = plt.subplots(figsize=(9, 5.5))
    b1 = ax.bar(x - w / 2, written, w, label="Written Premium", color="#2563EB", alpha=0.85, zorder=3)
    b2 = ax.bar(x + w / 2, earned,  w, label="Earned Premium",  color="#7C3AED", alpha=0.85, zorder=3)

    for bars in [b1, b2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 40,
                    f"€{bar.get_height():,.0f}", ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold")

    for xi, (w_, e_) in enumerate(zip(written, earned)):
        ax.annotate(f"Δ €{w_ - e_:,.0f}", xy=(xi, (w_ + e_) / 2), ha="center", va="center",
                    fontsize=8, color="#6B7280",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7))

    ax.set_xticks(x)
    ax.set_xticklabels(MONTH_LABELS, fontsize=11)
    ax.set_ylabel("Premium (EUR)", fontsize=11)
    ax.set_title("Written vs. Earned Premium — All Parties Combined\n"
                 "(Earned = proration by days remaining in month)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"€{v:,.0f}"))
    ax.set_ylim(0, 9500)
    fig.tight_layout()
    save(fig, "02_written_vs_earned_premium.png")


def chart_03_finance_vs_accounting():
    fig, axes = plt.subplots(1, 4, figsize=(15, 5.5), sharey=False)

    for ax, party in zip(axes, PARTIES):
        finance_vals    = [MONTHLY_PREMIUMS.get((party, m), (0, 0, 0))[0] for m in MONTHS]
        accounting_vals = [ACCOUNTING.get((party, m), 0) for m in MONTHS]
        x, w = np.arange(len(MONTHS)), 0.32

        ax.bar(x - w / 2, accounting_vals, w, label="Accounting",
               color=ACCOUNTING_COLOR, alpha=0.85, zorder=3)
        ax.bar(x + w / 2, finance_vals, w, label="Finance",
               color=FINANCE_COLOR, alpha=0.85, zorder=3)

        for xi, (acc, fin) in enumerate(zip(accounting_vals, finance_vals)):
            delta = fin - acc
            color = "#22C55E" if delta >= -0.01 else "#EF4444"
            sign = "+" if delta >= 0 else ""
            ax.text(xi, max(acc, fin) + 30, f"{sign}{delta:.2f}",
                    ha="center", va="bottom", fontsize=8, color=color, fontweight="bold")

        ax.set_title(party.capitalize(), fontsize=11, fontweight="bold",
                     color=PARTY_COLORS[party])
        ax.set_xticks(x)
        ax.set_xticklabels(["Jun", "Jul", "Aug"], fontsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"€{v:,.0f}"))
        if ax == axes[0]:
            ax.set_ylabel("Premium (EUR)", fontsize=10)
        ax.set_ylim(0, max(max(finance_vals), max(accounting_vals)) * 1.22)
        ax.grid(axis="y", alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    handles = [
        mpatches.Patch(color=ACCOUNTING_COLOR, label="Accounting (benchmark)"),
        mpatches.Patch(color=FINANCE_COLOR,    label="Finance (Gold layer)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=10,
               frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Finance vs. Accounting Premium — Reconciliation View\n"
                 "(delta = Finance − Accounting)", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "03_finance_vs_accounting.png")


def chart_04_delta_waterfall():
    labels, deltas, statuses = [], [], []
    for party in PARTIES:
        for m in MONTHS:
            status, delta = RECON_STATUS.get((party, m), ("MATCH", 0))
            labels.append(f"{party[:4]}.\n{m[5:]}")
            deltas.append(delta)
            statuses.append(status)

    status_color_map = {"MATCH": "#16A34A", "NEAR_MATCH": "#F59E0B", "DISCREPANCY": "#DC2626"}
    colors = [status_color_map[s] for s in statuses]

    fig, ax = plt.subplots(figsize=(13, 5.5))
    x = np.arange(len(labels))
    ax.axhline(0, color="#374151", linewidth=1.2, zorder=2)
    ax.bar(x, deltas, color=colors, alpha=0.85, zorder=3, width=0.6)

    for xi, (d, s) in enumerate(zip(deltas, statuses)):
        if d != 0:
            ax.text(xi, d - 0.3 if d < 0 else d + 0.1, f"€{d:+.2f}",
                    ha="center", va="top" if d < 0 else "bottom",
                    fontsize=8, fontweight="bold", color=status_color_map[s])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Delta: Finance − Accounting (EUR)", fontsize=10)
    ax.set_title("Reconciliation Delta by Party & Month\n"
                 "Total absolute discrepancy: €37.94  (filter: status = processed)",
                 fontsize=12, fontweight="bold", pad=12)

    legend_handles = [
        mpatches.Patch(color="#16A34A", label="MATCH (€0.00)"),
        mpatches.Patch(color="#F59E0B", label="NEAR_MATCH (< 1%)"),
        mpatches.Patch(color="#DC2626", label="DISCREPANCY (≥ 1%)"),
    ]
    ax.legend(handles=legend_handles, fontsize=9, loc="lower right")
    fig.tight_layout()
    save(fig, "04_reconciliation_delta.png")


def chart_05_status_matrix():
    from matplotlib.colors import ListedColormap
    status_map = {"MATCH": 0, "NEAR_MATCH": 1, "DISCREPANCY": 2}
    cmap = ListedColormap(["#16A34A", "#F59E0B", "#DC2626"])

    matrix       = np.zeros((len(PARTIES), len(MONTHS)), dtype=int)
    delta_matrix = np.zeros((len(PARTIES), len(MONTHS)))

    for i, party in enumerate(PARTIES):
        for j, m in enumerate(MONTHS):
            status, delta = RECON_STATUS.get((party, m), ("MATCH", 0))
            matrix[i, j]       = status_map[status]
            delta_matrix[i, j] = delta

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=2, aspect="auto")

    for i in range(len(PARTIES)):
        for j in range(len(MONTHS)):
            status = list(status_map.keys())[matrix[i, j]]
            delta  = delta_matrix[i, j]
            ax.text(j, i, f"{status}\n€{delta:+.2f}" if delta != 0 else f"{status}\n€0.00",
                    ha="center", va="center", fontsize=9, fontweight="bold", color="white")

    ax.set_xticks(range(len(MONTHS)))
    ax.set_xticklabels(MONTH_LABELS, fontsize=10)
    ax.set_yticks(range(len(PARTIES)))
    ax.set_yticklabels([p.capitalize() for p in PARTIES], fontsize=10)
    ax.set_title("Reconciliation Status Matrix\n"
                 "7 MATCH · 4 NEAR_MATCH · 1 DISCREPANCY  (total Δ €37.94)",
                 fontsize=12, fontweight="bold", pad=12)

    legend_handles = [
        mpatches.Patch(color="#16A34A", label="MATCH"),
        mpatches.Patch(color="#F59E0B", label="NEAR_MATCH"),
        mpatches.Patch(color="#DC2626", label="DISCREPANCY"),
    ]
    ax.legend(handles=legend_handles, loc="upper center",
              bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=9, frameon=False)
    fig.tight_layout()
    save(fig, "05_reconciliation_status_matrix.png")


def chart_06_transaction_status():
    labels, proc_vals, ref_vals, fail_vals = [], [], [], []
    for party in PARTIES:
        for m in MONTHS:
            labels.append(f"{party[:4]}.\n{m[5:]}")
            proc_vals.append(TXN_SUMMARY.get((party, m, "processed"), (0, 0))[0])
            ref_vals.append(TXN_SUMMARY.get((party, m, "refunded"),  (0, 0))[0])
            fail_vals.append(TXN_SUMMARY.get((party, m, "failed"),   (0, 0))[0])

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.bar(x, proc_vals, label="processed", color=STATUS_COLORS["processed"], alpha=0.88, zorder=3)
    ax.bar(x, ref_vals,  bottom=proc_vals,  label="refunded",  color=STATUS_COLORS["refunded"],  alpha=0.88, zorder=3)
    ax.bar(x, fail_vals, bottom=[p + r for p, r in zip(proc_vals, ref_vals)],
           label="failed", color=STATUS_COLORS["failed"], alpha=0.88, zorder=3)

    for xi, (p, r, f) in enumerate(zip(proc_vals, ref_vals, fail_vals)):
        ax.text(xi, p + r + f + 3, str(p + r + f),
                ha="center", va="bottom", fontsize=7.5, color="#374151")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Transaction Count", fontsize=10)
    ax.set_title("Transaction Volume by Status — Party & Month",
                 fontsize=12, fontweight="bold", pad=12)
    ax.legend(fontsize=10, loc="upper right")
    fig.tight_layout()
    save(fig, "06_transaction_status_breakdown.png")


def chart_07_premium_by_status():
    labels, proc_vals, ref_vals, fail_vals = [], [], [], []
    for party in PARTIES:
        for m in MONTHS:
            labels.append(f"{party[:4]}.\n{m[5:]}")
            proc_vals.append(TXN_SUMMARY.get((party, m, "processed"), (0, 0))[1])
            ref_vals.append(TXN_SUMMARY.get((party, m, "refunded"),  (0, 0))[1])
            fail_vals.append(TXN_SUMMARY.get((party, m, "failed"),   (0, 0))[1])

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.bar(x, proc_vals, label="processed", color=STATUS_COLORS["processed"], alpha=0.88, zorder=3)
    ax.bar(x, ref_vals,  bottom=proc_vals,  label="refunded",  color=STATUS_COLORS["refunded"],  alpha=0.88, zorder=3)
    ax.bar(x, fail_vals, bottom=[p + r for p, r in zip(proc_vals, ref_vals)],
           label="failed", color=STATUS_COLORS["failed"], alpha=0.88, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Premium Amount (EUR)", fontsize=10)
    ax.set_title("Premium EUR by Status — Party & Month\n"
                 "(Gold uses 'processed' only; refunded & failed shown for context)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.legend(fontsize=10, loc="upper right")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"€{v:,.0f}"))
    fig.tight_layout()
    save(fig, "07_premium_by_status_stacked.png")


def chart_08_date_spine_concept():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(6, 9.5, "KPI Data Mart — Date Spine Design",
            ha="center", va="center", fontsize=14, fontweight="bold")

    box_in = dict(boxstyle="round,pad=0.5", fc="#EFF6FF", ec="#2563EB", lw=1.5)
    ax.text(2.2, 8.3, "INPUT: 1 Customer Row",
            ha="center", va="center", fontsize=10, fontweight="bold", color="#1E40AF")
    ax.text(2.2, 7.1,
            "user_id     = USR002\nstarted_at  = 2025-02-01\nchuned_at   = 2025-04-30\nmonthly_premium = €14.99",
            ha="center", va="center", fontsize=8.5, fontfamily="monospace", bbox=box_in)

    ax.annotate("", xy=(5.2, 6.5), xytext=(3.9, 7.0),
                arrowprops=dict(arrowstyle="->", lw=2, color="#374151"))
    ax.text(4.55, 6.9, "generate_series(\n  started_at → churned_at\n  INTERVAL 1 day\n)",
            ha="center", va="center", fontsize=8, fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="#F0FDF4", ec="#16A34A", lw=1.2))

    box_out = dict(boxstyle="round,pad=0.4", fc="#FFFBEB", ec="#F59E0B", lw=1.5)
    ax.text(8.5, 8.3, "OUTPUT: 89 Daily Rows",
            ha="center", va="center", fontsize=10, fontweight="bold", color="#92400E")
    ax.text(8.5, 6.9,
            "activity_date | user_id | product_group | daily_premium\n"
            "─────────────────────────────────────────────────────\n"
            "2025-02-01    | USR002  | liability     | €0.535357\n"
            "2025-02-02    | USR002  | liability     | €0.535357\n"
            "    ...       |   ...   |     ...       |    ...\n"
            "2025-04-30    | USR002  | liability     | €0.499667",
            ha="center", va="center", fontsize=7.8, fontfamily="monospace", bbox=box_out)

    kpi_configs = [
        (1.5, 4.5, "KPI 1: Active Customers\nCOUNT(user_id)\nWHERE date = X", "#DBEAFE", "#2563EB"),
        (5.0, 4.5, "KPI 2: Premium in Range\nSUM(daily_premium)\nWHERE date BETWEEN A AND B", "#D1FAE5", "#16A34A"),
        (9.2, 4.5, "KPI 3: Accumulated Premium\nSUM(daily_premium)\nWHERE date ≤ target", "#EDE9FE", "#7C3AED"),
    ]
    for bx, by, btxt, fc, ec in kpi_configs:
        ax.text(bx, by, btxt, ha="center", va="center", fontsize=8.5, fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.5", fc=fc, ec=ec, lw=1.5))
        ax.annotate("", xy=(bx, 5.5), xytext=(8.5, 6.3),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color=ec,
                                   connectionstyle="arc3,rad=0.2"))

    ax.text(6, 2.8,
            "Production scale: 1M customers × 3yr avg tenure ≈ 1.1B rows\n"
            "Mitigation: partition by activity_month  +  dbt incremental (delete+insert)",
            ha="center", va="center", fontsize=9, color="#6B7280",
            bbox=dict(boxstyle="round,pad=0.4", fc="#F9FAFB", ec="#D1D5DB", lw=1))
    ax.text(6, 1.6,
            "Retroactive churn: DELETE rows after new churn date  +  re-INSERT  →  no full recompute",
            ha="center", va="center", fontsize=8.5, color="#92400E",
            bbox=dict(boxstyle="round,pad=0.4", fc="#FEF3C7", ec="#F59E0B", lw=1))

    fig.tight_layout()
    save(fig, "08_kpi_date_spine_concept.png")


def chart_09_total_premium_summary():
    totals = {party: sum(MONTHLY_PREMIUMS.get((party, m), (0, 0, 0))[0] for m in MONTHS)
              for party in PARTIES}
    sorted_parties = sorted(totals, key=totals.get, reverse=True)
    vals   = [totals[p] for p in sorted_parties]
    colors = [PARTY_COLORS[p] for p in sorted_parties]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh([p.capitalize() for p in sorted_parties], vals,
                   color=colors, alpha=0.88, zorder=3, height=0.5)

    for bar, v in zip(bars, vals):
        ax.text(v + 40, bar.get_y() + bar.get_height() / 2,
                f"€{v:,.2f}", va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("Total Written Premium Jun–Aug 2025 (EUR)", fontsize=10)
    ax.set_title("Total Written Premium by Party (Jun–Aug 2025)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"€{v:,.0f}"))
    ax.set_xlim(0, max(vals) * 1.18)
    fig.tight_layout()
    save(fig, "09_total_premium_summary.png")


def chart_10_delta_pct():
    delta_pct_map = {
        ("berlinre",   "2025-06"): 0.4564,
        ("berlinre",   "2025-07"): 1.3051,
        ("berlinre",   "2025-08"): 0.0,
        ("dronant",    "2025-06"): 0.0,
        ("dronant",    "2025-07"): 0.4657,
        ("dronant",    "2025-08"): 0.5492,
        ("getland",    "2025-06"): 0.0,
        ("getland",    "2025-07"): 0.0,
        ("getland",    "2025-08"): 0.0,
        ("liadigital", "2025-06"): 0.1097,
        ("liadigital", "2025-07"): 0.0,
        ("liadigital", "2025-08"): 0.0,
    }
    status_color_map = {"MATCH": "#16A34A", "NEAR_MATCH": "#F59E0B", "DISCREPANCY": "#DC2626"}
    labels, pcts, colors = [], [], []
    for party in PARTIES:
        for m in MONTHS:
            status, _ = RECON_STATUS.get((party, m), ("MATCH", 0))
            labels.append(f"{party[:4]}.\n{m[5:]}")
            pcts.append(delta_pct_map.get((party, m), 0))
            colors.append(status_color_map[status])

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.axhline(1.0, color="#DC2626", linewidth=1.2, linestyle="--",
               label="1% materiality threshold", alpha=0.7)
    ax.axhline(0.0, color="#374151", linewidth=0.8)
    ax.scatter(x, pcts, c=colors, s=110, zorder=4)

    for xi, (pct, color) in enumerate(zip(pcts, colors)):
        ax.vlines(xi, 0, pct, color=color, linewidth=1.5, alpha=0.6, zorder=3)
        if pct > 0:
            ax.text(xi, pct + 0.04, f"{pct:.2f}%",
                    ha="center", va="bottom", fontsize=8, fontweight="bold", color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Absolute Delta %", fontsize=9)
    ax.set_title("Reconciliation Delta % by Party & Month\n"
                 "(dashed = 1% materiality threshold)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(-0.1, 1.8)
    legend_handles = [
        mpatches.Patch(color="#16A34A", label="MATCH"),
        mpatches.Patch(color="#F59E0B", label="NEAR_MATCH"),
        mpatches.Patch(color="#DC2626", label="DISCREPANCY"),
        plt.Line2D([0], [0], color="#DC2626", linestyle="--", label="1% materiality"),
    ]
    ax.legend(handles=legend_handles, fontsize=9, loc="upper right")
    fig.tight_layout()
    save(fig, "10_reconciliation_delta_pct.png")


if __name__ == "__main__":
    print("Generating charts...")
    chart_01_monthly_written_premium()
    chart_02_written_vs_earned()
    chart_03_finance_vs_accounting()
    chart_04_delta_waterfall()
    chart_05_status_matrix()
    chart_06_transaction_status()
    chart_07_premium_by_status()
    chart_08_date_spine_concept()
    chart_09_total_premium_summary()
    chart_10_delta_pct()
    print(f"\nAll charts saved to: {OUT}")
