"""Load the SAP table extracts into DuckDB, run every query in ./sql, save results and charts.

Usage:
    python generate_data.py   # only if ./data is missing (it is committed to the repo)
    python analysis.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

ROOT = Path(__file__).parent
DATA, SQL, RESULTS, CHARTS = (ROOT / p for p in ("data", "sql", "results", "charts"))
RESULTS.mkdir(exist_ok=True)
CHARTS.mkdir(exist_ok=True)

# SAP keys keep their leading zeros, so document numbers and keys are loaded as text.
# Empty SAP fields (e.g. no rejection reason ABGRU) load as NULL.
KEY_COLS = {"VBELN", "KUNNR", "KUNAG", "LIFNR", "MATNR", "BELNR", "AUGBL", "VGBEL", "AUBEL", "EBELN", "BANFN",
            "MBLNR", "XBLNR", "WERKS", "VSTEL", "EKGRP", "BUKRS", "VKORG", "VTWEG", "SPART", "BWART", "ABGRU",
            "BWKEY", "KTOKD", "EKORG", "INFNR", "BNFPL"}
DATE_COLS = {"ERDAT", "VDATU", "LFDAT", "WADAT_IST", "FKDAT", "BUDAT", "ZFBDT", "AUGDT", "BADAT", "BEDAT",
             "EINDT", "BUDAT_MKPF", "BLDAT"}

con = duckdb.connect(str(ROOT / "sap.duckdb"))
for f in sorted(DATA.glob("*.csv")):
    cols = pd.read_csv(f, nrows=0).columns
    types = {c: "VARCHAR" for c in cols if c in KEY_COLS} | {c: "DATE" for c in cols if c in DATE_COLS}
    con.execute(f"CREATE OR REPLACE TABLE {f.stem} AS SELECT * FROM read_csv('{f.as_posix()}', header=true, "
                f"auto_detect=true, types={types!r})")

res = {}
for area in ("o2c", "p2p"):
    for f in sorted((SQL / area).glob("*.sql")):
        key = f"{area}_{f.stem}"
        df = con.execute(f.read_text()).df()
        res[key] = df
        df.to_csv(RESULTS / f"{key}.csv", index=False)
        print(f"\n=== {key}\n{df.to_string(index=False)}")

# ------------------------------------------------------------------ charts
BLUE, ORANGE, AQUA, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#b8b7b0", "#0b0b0b", "#52514e"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRAY, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e7e6e1", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.dpi": 150, "savefig.bbox": "tight",
})


def title(ax, main, sub):
    ax.set_title(main, loc="left", fontsize=13, fontweight="bold", color=INK, pad=22)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9.5, color=MUTED)


# 1. On-time shipping by plant over time
m = res["o2c_05_on_time_by_month"]
m = m[m["month"] < "2026-06-01"]  # June 2026 is incomplete at the extract date
names = {"1100": "Toronto", "1200": "Montreal", "1300": "Calgary"}
fig, ax = plt.subplots(figsize=(9, 4))
for plant, color in zip(["1100", "1300", "1200"], [BLUE, AQUA, ORANGE]):
    s = m[m["plant"] == plant]
    ax.plot(s["month"], s["pct_on_time"], color=color, lw=2)
    ax.text(s["month"].iloc[-1] + pd.Timedelta(days=12), s["pct_on_time"].iloc[-1], names[plant],
            va="center", color=INK, fontsize=9)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_ylim(0, 100)
title(ax, "Montreal ships late far more often than the other plants",
      "% of deliveries shipped on or before the customer's requested date, by month")
fig.savefig(CHARTS / "o2c_on_time_by_plant.png"); plt.close(fig)

# 2. O2C cycle time by plant (stacked steps)
c = res["o2c_03_cycle_time_by_plant"]
c = c[c["plant"] != "All plants"].iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 3.2))
left = 0
for col, color, label in [("order_to_ship_days", ORANGE, "Order → ship"), ("ship_to_bill_days", GRAY, "Ship → bill"),
                          ("bill_to_cash_days", BLUE, "Bill → cash")]:
    ax.barh(c["plant"], c[col], left=left, color=color, height=0.55, label=label, edgecolor="white", linewidth=2)
    left = left + c[col].values
for y, total in enumerate(c["total_o2c_days"]):
    ax.text(total + 0.8, y, f"{total:.0f} days", va="center", fontsize=9, color=INK)
ax.set_xlabel("Average days")
ax.grid(axis="y", visible=False)
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
title(ax, "Order to cash takes about 7 weeks, mostly waiting for payment", "Average days per step, paid orders. Montreal needs ~3 extra days to ship")
fig.savefig(CHARTS / "o2c_cycle_time.png"); plt.close(fig)

# 3. Late-paying customers
lp = res["o2c_06_customer_payment_behaviour"].iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.barh(lp["name"], lp["avg_days_past_due"], color=[ORANGE if x > 15 else BLUE for x in lp["avg_days_past_due"]], height=0.6)
for y, (x, t_) in enumerate(zip(lp["avg_days_past_due"], lp["terms"])):
    ax.text(x + 0.4, y, f"{x:.0f} days  ({t_})", va="center", fontsize=9, color=INK)
ax.set_xlabel("Average days paid after the due date")
ax.set_xlim(0, lp["avg_days_past_due"].max() * 1.25)
ax.grid(axis="y", visible=False)
title(ax, "Six customers pay about four weeks late, every time", "Average days past due on cleared invoices (BSAD), 10 slowest payers with 20+ invoices")
fig.savefig(CHARTS / "o2c_late_payers.png"); plt.close(fig)

# 4. Vendor on-time
v = res["p2p_02_vendor_on_time"].head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 4.2))
cut = res["p2p_02_vendor_on_time"]["pct_late"].median()
ax.barh(v["name"] + " (" + v["country"] + ")", v["pct_late"], color=[ORANGE if x > 20 else BLUE for x in v["pct_late"]], height=0.6)
for y, x in enumerate(v["pct_late"]):
    ax.text(x + 0.6, y, f"{x}%", va="center", fontsize=9, color=INK)
ax.axvline(cut, color=MUTED, lw=1, ls="--")
ax.text(cut + 0.5, len(v) - 0.4, f"median vendor {cut:.0f}%", color=MUTED, fontsize=8.5)
ax.xaxis.set_major_formatter(mtick.PercentFormatter())
ax.grid(axis="y", visible=False)
title(ax, "Three vendors deliver late far more often than the rest", "% of goods receipts more than 2 days after the promised date, 10 least reliable vendors")
fig.savefig(CHARTS / "p2p_vendor_on_time.png"); plt.close(fig)

# 5. Three-way match
t = res["p2p_03_three_way_match"]
t = t[t["match_result"] != "Matched"].iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 2.8))
ax.barh(t["match_result"], t["invoices"], color=ORANGE, height=0.55)
for y, (n, o) in enumerate(zip(t["invoices"], t["overbilled_cad"])):
    ax.text(n + t["invoices"].max() * 0.02, y, f"{n} invoices · ${o:,.0f} over", va="center", fontsize=9, color=INK)
ax.set_xlim(0, t["invoices"].max() * 1.6)
ax.grid(axis="y", visible=False)
title(ax, "Three-way match exceptions", "Vendor invoices that don't match the PO price or the goods received")
fig.savefig(CHARTS / "p2p_three_way_match.png"); plt.close(fig)

print("\nCharts written to", CHARTS)
