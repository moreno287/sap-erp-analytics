-- Vendor delivery reliability: goods receipt date (MSEG, movement type 101) vs promised date (EKET.EINDT).
-- "Late" = more than 2 days after the promised date. Vendors with 50+ receipts.
WITH gr AS (
    SELECT m.LIFNR, m.EBELN, m.EBELP,
           DATE_DIFF('day', t.EINDT, m.BUDAT_MKPF) AS days_late,
           m.MENGE AS gr_qty, p.MENGE AS po_qty
    FROM MSEG m
    JOIN EKET t ON t.EBELN = m.EBELN AND t.EBELP = m.EBELP
    JOIN EKPO p ON p.EBELN = m.EBELN AND p.EBELP = m.EBELP
    JOIN EKKO k ON k.EBELN = m.EBELN
    WHERE m.BWART = '101'
      AND k.BEDAT <= m.BUDAT_MKPF              -- exclude after-the-fact POs (see 04_maverick_buying)
)
SELECT g.LIFNR                                                          AS vendor,
       v.NAME1                                                          AS name,
       v.LAND1                                                          AS country,
       COUNT(*)                                                         AS receipts,
       ROUND(100 * AVG(CASE WHEN days_late > 2 THEN 1 ELSE 0 END), 1)   AS pct_late,
       ROUND(AVG(CASE WHEN days_late > 2 THEN days_late END), 1)         AS avg_days_late_when_late,
       ROUND(100 * AVG(CASE WHEN gr_qty < po_qty THEN 1 ELSE 0 END), 1) AS pct_short_delivered
FROM gr g JOIN LFA1 v USING (LIFNR)
GROUP BY ALL
HAVING COUNT(*) >= 50
ORDER BY pct_late DESC;
