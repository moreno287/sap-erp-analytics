-- Which vendors cause the price mismatches? Share of invoices >1% above PO price, before and after Jan 2025.
WITH m AS (
    SELECT i.LIFNR, i.BLDAT,
           r.WRBTR - r.MENGE * p.NETPR                                     AS price_diff,
           CASE WHEN r.WRBTR / r.MENGE > p.NETPR * 1.01 THEN 1 ELSE 0 END  AS price_flag
    FROM RSEG r
    JOIN RBKP i ON i.BELNR = r.BELNR
    JOIN EKPO p ON p.EBELN = r.EBELN AND p.EBELP = r.EBELP
)
SELECT m.LIFNR                                                                AS vendor,
       v.NAME1                                                                AS name,
       COUNT(*)                                                               AS invoices,
       ROUND(100 * AVG(CASE WHEN BLDAT <  DATE '2025-01-01' THEN price_flag END), 1) AS pct_mismatch_2024,
       ROUND(100 * AVG(CASE WHEN BLDAT >= DATE '2025-01-01' THEN price_flag END), 1) AS pct_mismatch_2025_26,
       ROUND(SUM(GREATEST(price_diff, 0)), 0)                                 AS overbilled_cad
FROM m JOIN LFA1 v USING (LIFNR)
GROUP BY ALL
ORDER BY overbilled_cad DESC
LIMIT 5;
