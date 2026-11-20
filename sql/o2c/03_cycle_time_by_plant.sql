-- Order-to-cash cycle time per step, by shipping plant. Paid orders only.
WITH flow AS (
    SELECT DISTINCT
           a.VBELN                    AS sales_order,
           l.VSTEL                    AS plant,
           a.ERDAT                    AS order_date,
           l.WADAT_IST                AS goods_issue_date,
           k.FKDAT                    AS billing_date,
           b.AUGDT                    AS payment_date
    FROM VBAK a
    JOIN LIPS lp ON lp.VGBEL = a.VBELN
    JOIN LIKP l  ON l.VBELN  = lp.VBELN
    JOIN VBRP rp ON rp.VGBEL = l.VBELN
    JOIN VBRK k  ON k.VBELN  = rp.VBELN
    JOIN BSAD b  ON b.VBELN  = k.VBELN
)
SELECT f.plant || ' ' || w.NAME1                                           AS plant,
       COUNT(*)                                                             AS orders,
       ROUND(AVG(DATE_DIFF('day', order_date, goods_issue_date)), 1)        AS order_to_ship_days,
       ROUND(AVG(DATE_DIFF('day', goods_issue_date, billing_date)), 1)      AS ship_to_bill_days,
       ROUND(AVG(DATE_DIFF('day', billing_date, payment_date)), 1)          AS bill_to_cash_days,
       ROUND(AVG(DATE_DIFF('day', order_date, payment_date)), 1)            AS total_o2c_days
FROM flow f
JOIN T001W w ON w.WERKS = f.plant
GROUP BY 1
UNION ALL
SELECT 'All plants', COUNT(*),
       ROUND(AVG(DATE_DIFF('day', order_date, goods_issue_date)), 1),
       ROUND(AVG(DATE_DIFF('day', goods_issue_date, billing_date)), 1),
       ROUND(AVG(DATE_DIFF('day', billing_date, payment_date)), 1),
       ROUND(AVG(DATE_DIFF('day', order_date, payment_date)), 1)
FROM flow
ORDER BY plant;
