-- Accounts receivable aging at the extract date (open items in BSID), like report S_ALR_87012178.
WITH open_items AS (
    SELECT b.*, c.NAME1,
           DATE_DIFF('day', ZFBDT + ZBD1T * INTERVAL 1 DAY, DATE '2026-06-30') AS days_overdue
    FROM BSID b JOIN KNA1 c USING (KUNNR)
)
SELECT CASE WHEN days_overdue <= 0  THEN '1. Not yet due'
            WHEN days_overdue <= 30 THEN '2. 1-30 days overdue'
            WHEN days_overdue <= 60 THEN '3. 31-60 days overdue'
            WHEN days_overdue <= 90 THEN '4. 61-90 days overdue'
            ELSE                         '5. 90+ days overdue' END            AS aging_bucket,
       COUNT(*)                                                             AS open_items,
       ROUND(SUM(DMBTR), 0)                                                 AS open_amount_cad,
       ROUND(100 * SUM(DMBTR) / SUM(SUM(DMBTR)) OVER (), 1)                 AS pct_of_ar
FROM open_items
GROUP BY 1
ORDER BY 1;
