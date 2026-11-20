"""Generate a synthetic SAP S/4HANA-style dataset for a fictional Canadian distributor.

Real SAP data is never public, so this script simulates one company's ERP extract using SAP's own table
and field names (KNA1, VBAK, LIKP, VBRK, BSAD, EKKO, EKPO, MSEG, RBKP ...). The output is a set of CSVs in
./data, one per SAP table, that the SQL in ./sql analyses as if it came from a real system.

Company: "Maple Industrial Supply Inc." (company code 1000, currency CAD), 3 plants:
1100 Toronto, 1200 Montreal, 1300 Calgary. Period: Jan 2024 – Jun 2026, extract date 30 Jun 2026.

The simulation includes a few realistic operational problems on purpose (some customers pay late,
one plant ships late more often, some vendors are unreliable, some purchases are made without a PO first).
The analysis has to find them from the tables alone. Seed is fixed, so the data is reproducible.
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-06-30")
EXTRACT = END
DAYS = pd.date_range(START, END, freq="D")
BUSINESS_DAYS = DAYS[DAYS.weekday < 5]


def save(df, name):
    df.to_csv(OUT / f"{name}.csv", index=False)
    print(f"{name:<6} {len(df):>7,} rows")


def unique_names(first, middle, suffix, n):
    """n distinct company names built from word lists (no two share the same first + middle words)."""
    combos = [(a, b) for a in first for b in middle]
    picks = rng.choice(len(combos), n, replace=False)
    return [f"{combos[i][0]} {combos[i][1]} {rng.choice(suffix)}" for i in picks]


# --------------------------------------------------------------------------------------------------
# Master data
# --------------------------------------------------------------------------------------------------
PLANTS = pd.DataFrame({
    "WERKS": ["1100", "1200", "1300"],
    "NAME1": ["Toronto DC", "Montreal DC", "Calgary DC"],
    "REGIO": ["ON", "QC", "AB"],
})

MATKL = {  # material group: (name, typical unit cost range CAD)
    "FAST01": ("Fasteners", (0.5, 8)),
    "TOOL01": ("Hand tools", (12, 90)),
    "PWR01": ("Power tools", (80, 450)),
    "SAFE01": ("Safety equipment", (6, 60)),
    "WELD01": ("Welding supplies", (15, 220)),
    "ELEC01": ("Electrical", (4, 140)),
}
n_mat = 160
mat_groups = rng.choice(list(MATKL), n_mat, p=[0.22, 0.2, 0.1, 0.18, 0.14, 0.16])
MARA = pd.DataFrame({
    "MATNR": [f"MAT-{i:05d}" for i in range(10001, 10001 + n_mat)],
    "MTART": "HAWA",  # trading goods
    "MATKL": mat_groups,
    "MEINS": np.where(mat_groups == "FAST01", "BOX", "EA"),
})
MAKT = pd.DataFrame({
    "MATNR": MARA["MATNR"],
    "SPRAS": "E",
    "MAKTX": [f"{MATKL[g][0]} item {i:03d}" for i, g in enumerate(mat_groups, 1)],
})
lo = np.array([MATKL[g][1][0] for g in mat_groups])
hi = np.array([MATKL[g][1][1] for g in mat_groups])
MBEW = pd.DataFrame({  # valuation: standard price
    "MATNR": MARA["MATNR"], "BWKEY": "1100", "VPRSV": "S",
    "STPRS": np.round(np.exp(rng.uniform(np.log(lo), np.log(hi))), 2),
})
# Popularity of each material (some sell far more than others)
mat_pop = rng.pareto(1.3, n_mat) + 0.05
mat_pop /= mat_pop.sum()

# Customers
n_cust = 60
regions = rng.choice(["ON", "QC", "AB", "BC", "MB", "NS"], n_cust, p=[0.42, 0.22, 0.14, 0.12, 0.05, 0.05])
industries = ["Construction", "Manufacturing", "Utilities", "Mining", "Facilities"]
KNA1 = pd.DataFrame({
    "KUNNR": [f"{i:010d}" for i in range(100001, 100001 + n_cust)],
    "NAME1": unique_names(["Northern", "Great Lakes", "Prairie", "Atlantic", "Summit", "Harbour", "Pioneer",
                           "Laurentian", "Rideau", "Granite", "Boreal", "Maritime"],
                          industries, ["Ltd.", "Inc.", "Corp.", "Group"], n_cust),
    "LAND1": "CA",
    "REGIO": regions,
    "KTOKD": "0001",
})
KNA1["BRSCH"] = KNA1["NAME1"].str.split().str[-2]  # industry key
KNB1 = pd.DataFrame({
    "KUNNR": KNA1["KUNNR"], "BUKRS": "1000",
    "ZTERM": rng.choice(["NT30", "NT45", "NT60"], n_cust, p=[0.6, 0.25, 0.15]),
})
cust_weight = rng.lognormal(0, 1.1, n_cust)
cust_weight /= cust_weight.sum()
late_payers = set(rng.choice(KNA1["KUNNR"], 6, replace=False))
# Nearest plant to each customer's region
plant_for_region = {"ON": "1100", "MB": "1100", "NS": "1200", "QC": "1200", "AB": "1300", "BC": "1300"}

# Vendors
n_vend = 28
LFA1 = pd.DataFrame({
    "LIFNR": [f"{i:010d}" for i in range(300001, 300001 + n_vend)],
    "NAME1": unique_names(["Apex", "Delta", "Ironclad", "Keystone", "Meridian", "Titan", "Vector", "Orion",
                           "Crown", "Falcon"], ["Supply", "Manufacturing", "Industries", "Tools", "Components"],
                          ["Ltd.", "Inc.", "Co.", "LLC"], n_vend),
    "LAND1": rng.choice(["CA", "US", "CN", "DE"], n_vend, p=[0.45, 0.35, 0.12, 0.08]),
})
LFB1 = pd.DataFrame({"LIFNR": LFA1["LIFNR"], "BUKRS": "1000",
                     "ZTERM": rng.choice(["NT30", "NT45", "NT60"], n_vend, p=[0.5, 0.3, 0.2])})
vendor_lead = np.where(LFA1["LAND1"].isin(["CN", "DE"]), rng.integers(28, 45, n_vend), rng.integers(5, 15, n_vend))
mat_vendor = rng.choice(LFA1["LIFNR"], n_mat)  # main vendor per material
EINA = pd.DataFrame({"INFNR": [f"53{i:08d}" for i in range(n_mat)], "MATNR": MARA["MATNR"], "LIFNR": mat_vendor})

# --------------------------------------------------------------------------------------------------
# Order-to-Cash: VBAK/VBAP -> LIKP/LIPS -> VBRK/VBRP -> BSAD/BSID
# --------------------------------------------------------------------------------------------------
month_season = {1: 0.8, 2: 0.85, 3: 1.0, 4: 1.1, 5: 1.2, 6: 1.2, 7: 1.05, 8: 1.05, 9: 1.1, 10: 1.0, 11: 0.9, 12: 0.7}
growth = np.linspace(1.0, 1.35, len(BUSINESS_DAYS))  # business grows ~35% over the period
w = np.array([month_season[x.month] for x in BUSINESS_DAYS]) * growth
orders_per_day = rng.poisson(w / w.mean() * 18)

vbak, vbap, likp, lips, vbrk, vbrp, bsad, bsid = ([] for _ in range(8))
so, dl, bl, fi = 1000000, 80000000, 90000000, 1400000000
price_index = {m: 1.0 for m in MARA["MATNR"]}
stprs = dict(zip(MBEW["MATNR"], MBEW["STPRS"]))
zterm = dict(zip(KNB1["KUNNR"], KNB1["ZTERM"]))
cust_region = dict(zip(KNA1["KUNNR"], KNA1["REGIO"]))
plant_gi_mean = {"1100": 2.0, "1200": 5.5, "1300": 3.0}  # Montreal is slower to pick & ship

for day, n in zip(BUSINESS_DAYS, orders_per_day):
    for _ in range(n):
        so += 1
        kunnr = rng.choice(KNA1["KUNNR"], p=cust_weight)
        werks = plant_for_region[cust_region[kunnr]]
        vdatu = day + pd.Timedelta(days=int(rng.choice([3, 5, 7, 10], p=[0.2, 0.35, 0.35, 0.1])))
        n_items = int(rng.integers(1, 6))
        mats = rng.choice(MARA["MATNR"], n_items, replace=False, p=mat_pop)
        cancelled = rng.random() < 0.025
        items = []
        for pos, m in enumerate(mats, 1):
            qty = int(max(1, rng.lognormal(2.2, 0.9)))
            netpr = round(stprs[m] * rng.uniform(1.25, 1.6) * (1.04 if day >= pd.Timestamp("2025-04-01") else 1.0), 2)
            items.append((pos * 10, m, qty, netpr))
            vbap.append({"VBELN": str(so), "POSNR": pos * 10, "MATNR": m, "WERKS": werks, "KWMENG": qty,
                         "VRKME": "EA", "NETPR": netpr, "NETWR": round(qty * netpr, 2), "WAERK": "CAD",
                         "ABGRU": "Z1" if cancelled else ""})
        netwr = round(sum(q * p for _, _, q, p in items), 2)
        vbak.append({"VBELN": str(so), "AUART": "OR", "VKORG": "1000", "VTWEG": "10", "SPART": "00",
                     "KUNNR": kunnr, "ERDAT": day.date(), "VDATU": vdatu.date(), "NETWR": netwr, "WAERK": "CAD"})
        if cancelled:
            continue
        # Delivery & goods issue
        gi_delay = rng.gamma(2.0, plant_gi_mean[werks] / 2.0) + rng.integers(1, 4)
        if rng.random() < 0.04:  # stock-out: waits for replenishment
            gi_delay += rng.integers(7, 25)
        gi = day + pd.Timedelta(days=int(round(gi_delay)))
        if gi > EXTRACT:
            continue
        dl += 1
        likp.append({"VBELN": str(dl), "LFART": "LF", "VSTEL": werks, "KUNNR": kunnr, "ERDAT": day.date(),
                     "LFDAT": vdatu.date(), "WADAT_IST": gi.date()})
        for pos, m, q, p in items:
            lips.append({"VBELN": str(dl), "POSNR": pos, "MATNR": m, "WERKS": werks, "LFIMG": q,
                         "VGBEL": str(so), "VGPOS": pos})
        # Billing
        fkdat = gi + pd.Timedelta(days=int(rng.choice([0, 1, 1, 2, 3])))
        if fkdat > EXTRACT:
            continue
        bl += 1
        vbrk.append({"VBELN": str(bl), "FKART": "F2", "FKDAT": fkdat.date(), "KUNAG": kunnr,
                     "NETWR": netwr, "MWSBK": round(netwr * 0.13, 2), "WAERK": "CAD", "BUKRS": "1000"})
        for pos, m, q, p in items:
            vbrp.append({"VBELN": str(bl), "POSNR": pos, "MATNR": m, "FKIMG": q, "NETWR": round(q * p, 2),
                         "VGBEL": str(dl), "VGPOS": pos, "AUBEL": str(so), "AUPOS": pos})
        # Accounting: customer open item, cleared when paid
        fi += 1
        terms = int(zterm[kunnr][2:])
        due = fkdat + pd.Timedelta(days=terms)
        if kunnr in late_payers:
            pay_delay = rng.normal(28, 12)
        else:
            pay_delay = rng.normal(1, 6) if rng.random() > 0.08 else rng.normal(20, 8)
        paid = due + pd.Timedelta(days=int(round(pay_delay)))
        paid = max(paid, fkdat + pd.Timedelta(days=3))
        row = {"BUKRS": "1000", "KUNNR": kunnr, "BELNR": str(fi), "GJAHR": fkdat.year, "BUDAT": fkdat.date(),
               "ZFBDT": fkdat.date(), "ZTERM": zterm[kunnr], "ZBD1T": terms, "VBELN": str(bl),
               "DMBTR": round(netwr * 1.13, 2), "WAERS": "CAD", "SHKZG": "S"}
        if paid <= EXTRACT:
            bsad.append({**row, "AUGDT": paid.date(), "AUGBL": str(fi + 500000000)})
        else:
            bsid.append(row)

save(PLANTS, "T001W"); save(MARA, "MARA"); save(MAKT, "MAKT"); save(MBEW, "MBEW")
save(KNA1, "KNA1"); save(KNB1, "KNB1"); save(LFA1, "LFA1"); save(LFB1, "LFB1"); save(EINA, "EINA")
save(pd.DataFrame(vbak), "VBAK"); save(pd.DataFrame(vbap), "VBAP")
save(pd.DataFrame(likp), "LIKP"); save(pd.DataFrame(lips), "LIPS")
save(pd.DataFrame(vbrk), "VBRK"); save(pd.DataFrame(vbrp), "VBRP")
save(pd.DataFrame(bsad), "BSAD"); save(pd.DataFrame(bsid), "BSID")

# --------------------------------------------------------------------------------------------------
# Procure-to-Pay: EBAN -> EKKO/EKPO/EKET -> MSEG (GR, mvt 101) -> RBKP/RSEG -> BSAK
# --------------------------------------------------------------------------------------------------
# Purchases follow sales volume per material (replenishment), batched into POs.
sold = pd.DataFrame(vbap).query("ABGRU == ''").groupby("MATNR")["KWMENG"].sum()
vendor_of = dict(zip(MARA["MATNR"], mat_vendor))
lead_of = dict(zip(LFA1["LIFNR"], vendor_lead))
vterms = dict(zip(LFB1["LIFNR"], LFB1["ZTERM"]))
ekgrp_pr_days = {"001": (1, 3), "002": (2, 5), "003": (4, 14)}  # purchasing group 003 is slow to convert PRs

eban, ekko, ekpo, eket, mseg, rbkp, rseg, bsak = ([] for _ in range(8))
pr, po, mb, inv, fiv = 10000000, 4500000000, 5000000000, 5105600000, 1900000000
po_days = BUSINESS_DAYS[BUSINESS_DAYS <= END - pd.Timedelta(days=5)]
n_pos = 5200
# Each PO is for one vendor and holds 1-4 of its materials
vend_mats = pd.Series(MARA["MATNR"].values, index=mat_vendor).groupby(level=0).apply(list).to_dict()
vend_weight = pd.Series(sold.reindex(MARA["MATNR"]).fillna(0).values * MBEW["STPRS"].values, index=mat_vendor).groupby(level=0).sum()
vend_weight = (vend_weight / vend_weight.sum()).reindex(LFA1["LIFNR"]).fillna(0)
vend_weight = (vend_weight + 0.005) / (vend_weight + 0.005).sum()
# Problem vendors are picked among the 12 biggest, so they matter to the business
top_vendors = vend_weight.sort_values(ascending=False).index[:12]
vendor_unreliable = set(rng.choice(top_vendors, 3, replace=False))
vendor_price_creep = rng.choice(sorted(set(top_vendors) - vendor_unreliable))

for _ in range(n_pos):
    po += 1
    lifnr = rng.choice(LFA1["LIFNR"], p=vend_weight.values)
    bedat = pd.Timestamp(rng.choice(po_days))
    ekgrp = rng.choice(list(ekgrp_pr_days), p=[0.5, 0.3, 0.2])
    werks = rng.choice(["1100", "1200", "1300"], p=[0.55, 0.27, 0.18])
    mats = list(rng.choice(vend_mats[lifnr], min(len(vend_mats[lifnr]), int(rng.integers(1, 5))), replace=False))
    maverick = rng.random() < 0.05  # PO raised after the vendor already invoiced
    eindt = bedat + pd.Timedelta(days=int(lead_of[lifnr]))
    ekko.append({"EBELN": str(po), "BSART": "NB", "BUKRS": "1000", "EKORG": "1000", "EKGRP": ekgrp,
                 "LIFNR": lifnr, "BEDAT": bedat.date(), "WAERS": "CAD", "ZTERM": vterms[lifnr]})
    lo_d, hi_d = ekgrp_pr_days[ekgrp]
    for pos, m in enumerate(mats, 1):
        ebelp = pos * 10
        qty = int(max(5, rng.lognormal(3.6, 0.7)))
        netpr = round(stprs[m] * rng.uniform(0.97, 1.03) * (1.05 if bedat >= pd.Timestamp("2025-04-01") else 1.0), 2)
        has_pr = not maverick and rng.random() < 0.9
        banfn = ""
        if has_pr:
            pr += 1
            banfn = str(pr)
            badat = bedat - pd.Timedelta(days=int(rng.integers(lo_d, hi_d + 1)))
            eban.append({"BANFN": banfn, "BNFPO": 10, "MATNR": m, "WERKS": werks, "MENGE": qty,
                         "BADAT": badat.date(), "EKGRP": ekgrp, "EBELN": str(po), "EBELP": ebelp})
        ekpo.append({"EBELN": str(po), "EBELP": ebelp, "MATNR": m, "WERKS": werks, "MENGE": qty, "MEINS": "EA",
                     "NETPR": netpr, "NETWR": round(qty * netpr, 2), "BANFN": banfn, "BNFPL": 10 if banfn else ""})
        eket.append({"EBELN": str(po), "EBELP": ebelp, "ETENR": 1, "EINDT": eindt.date(), "MENGE": qty})

        # Goods receipt
        if lifnr in vendor_unreliable:
            delay = rng.normal(6, 6) if rng.random() < 0.45 else rng.normal(0, 1.5)
        else:
            delay = rng.normal(5, 4) if rng.random() < 0.07 else rng.normal(-0.5, 1.5)
        gr_date = eindt + pd.Timedelta(days=int(round(delay)))
        if maverick:
            gr_date = bedat - pd.Timedelta(days=int(rng.integers(5, 20)))
        if gr_date > EXTRACT:
            continue
        gr_qty = qty if rng.random() > 0.05 else int(qty * rng.uniform(0.6, 0.95))
        mb += 1
        mseg.append({"MBLNR": str(mb), "MJAHR": gr_date.year, "ZEILE": 1, "BWART": "101", "MATNR": m,
                     "WERKS": werks, "LIFNR": lifnr, "MENGE": gr_qty, "EBELN": str(po), "EBELP": ebelp,
                     "BUDAT_MKPF": gr_date.date(), "DMBTR": round(gr_qty * netpr, 2)})
        # Vendor invoice
        bldat = gr_date + pd.Timedelta(days=int(rng.integers(0, 8)))
        if maverick:
            bldat = bedat - pd.Timedelta(days=int(rng.integers(1, 5)))
        if bldat > EXTRACT:
            continue
        inv_qty = gr_qty if rng.random() > 0.02 else qty  # some vendors bill the ordered, not received, qty
        if lifnr == vendor_price_creep and bedat >= pd.Timestamp("2025-01-01") and rng.random() < 0.6:
            inv_pr = round(netpr * rng.uniform(1.03, 1.09), 2)
        else:
            inv_pr = netpr if rng.random() > 0.03 else round(netpr * rng.uniform(1.01, 1.06), 2)
        inv += 1
        amount = round(inv_qty * inv_pr, 2)
        rbkp.append({"BELNR": str(inv), "GJAHR": bldat.year, "BLDAT": bldat.date(), "BUDAT": bldat.date(),
                     "LIFNR": lifnr, "RMWWR": amount, "WAERS": "CAD", "ZTERM": vterms[lifnr]})
        rseg.append({"BELNR": str(inv), "GJAHR": bldat.year, "BUZEI": 1, "EBELN": str(po), "EBELP": ebelp,
                     "MATNR": m, "MENGE": inv_qty, "WRBTR": amount})
        due = bldat + pd.Timedelta(days=int(vterms[lifnr][2:]))
        paid = due + pd.Timedelta(days=int(rng.normal(0, 3)))
        if paid <= EXTRACT:
            fiv += 1
            bsak.append({"BUKRS": "1000", "LIFNR": lifnr, "BELNR": str(fiv), "GJAHR": bldat.year,
                         "BUDAT": bldat.date(), "XBLNR": str(inv), "DMBTR": amount, "AUGDT": paid.date()})

save(pd.DataFrame(eban), "EBAN"); save(pd.DataFrame(ekko), "EKKO"); save(pd.DataFrame(ekpo), "EKPO")
save(pd.DataFrame(eket), "EKET"); save(pd.DataFrame(mseg), "MSEG"); save(pd.DataFrame(rbkp), "RBKP")
save(pd.DataFrame(rseg), "RSEG"); save(pd.DataFrame(bsak), "BSAK")
print("Done. Extract date:", EXTRACT.date())
