-- Who pays late? Days paid after the due date (baseline ZFBDT + payment term days ZBD1T), cleared items only.
WITH items AS (
    SELECT KUNNR,
           DMBTR,
           DATE_DIFF('day', ZFBDT + ZBD1T * INTERVAL 1 DAY, AUGDT) AS days_past_due
    FROM BSAD
)
SELECT i.KUNNR                                                       AS customer,
       c.NAME1                                                       AS name,
       t.ZTERM                                                       AS terms,
       COUNT(*)                                                      AS invoices_paid,
       ROUND(SUM(i.DMBTR), 0)                                        AS amount_paid_cad,
       ROUND(AVG(i.days_past_due), 1)                                AS avg_days_past_due,
       ROUND(100 * AVG(CASE WHEN i.days_past_due > 15 THEN 1 ELSE 0 END), 1) AS pct_paid_15plus_days_late
FROM items i
JOIN KNA1 c USING (KUNNR)
JOIN KNB1 t USING (KUNNR)
GROUP BY ALL
HAVING COUNT(*) >= 20
ORDER BY avg_days_past_due DESC
LIMIT 10;
