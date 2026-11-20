"""Export the data behind the interactive dashboard (https://moreno287.github.io/sap-dashboard/) to JSON.

Run after analysis.py (it reads sap.duckdb and results/).
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).parent
con = duckdb.connect(str(ROOT / "sap.duckdb"), read_only=True)
R = lambda name: pd.read_csv(ROOT / "results" / f"{name}.csv", dtype={"purchasing_group": str})

monthly = con.execute("""
    SELECT strftime(DATE_TRUNC('month', k.FKDAT), '%Y-%m') AS month, l.VSTEL AS plant, ROUND(SUM(p.NETWR), 0) AS revenue
    FROM VBRK k JOIN VBRP p ON p.VBELN = k.VBELN JOIN LIKP l ON l.VBELN = p.VGBEL
    GROUP BY 1, 2 ORDER BY 1, 2
""").df()
ontime = con.execute("""
    SELECT strftime(DATE_TRUNC('month', a.ERDAT), '%Y-%m') AS month, l.VSTEL AS plant,
           COUNT(*) AS deliveries, SUM(CASE WHEN l.WADAT_IST <= a.VDATU THEN 1 ELSE 0 END) AS on_time
    FROM LIKP l JOIN (SELECT DISTINCT VBELN, VGBEL FROM LIPS) lp ON lp.VBELN = l.VBELN JOIN VBAK a ON a.VBELN = lp.VGBEL
    WHERE a.ERDAT < DATE '2026-06-01'
    GROUP BY 1, 2 ORDER BY 1, 2
""").df()

match = R("p2p_03_three_way_match")
aging = R("o2c_07_ar_aging")
cycle = R("o2c_03_cycle_time_by_plant")
out = {
    "extract_date": "2026-06-30",
    "monthly_revenue": monthly.to_dict("records"),
    "on_time": ontime.to_dict("records"),
    "cycle": cycle.to_dict("records"),
    "late_payers": R("o2c_06_customer_payment_behaviour")[["name", "terms", "avg_days_past_due", "pct_paid_15plus_days_late"]].to_dict("records"),
    "vendors": R("p2p_02_vendor_on_time").head(10)[["name", "country", "receipts", "pct_late"]].to_dict("records"),
    "aging": aging.to_dict("records"),
    "match": match.to_dict("records"),
    "pr_to_po": R("p2p_01_pr_to_po_cycle").to_dict("records"),
    "dso": R("o2c_08_dso_by_quarter").to_dict("records"),
}
target = ROOT / "results" / "dashboard.json"
target.write_text(json.dumps(out, indent=1, default=str))
print("wrote", target)
