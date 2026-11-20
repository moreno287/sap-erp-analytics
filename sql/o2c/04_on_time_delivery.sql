-- On-time shipping: goods issue (LIKP.WADAT_IST) on or before the customer's requested date (VBAK.VDATU).
SELECT l.VSTEL || ' ' || w.NAME1                                                  AS plant,
       COUNT(*)                                                                    AS deliveries,
       ROUND(100 * AVG(CASE WHEN l.WADAT_IST <= a.VDATU THEN 1 ELSE 0 END), 1)    AS pct_on_time,
       ROUND(AVG(GREATEST(DATE_DIFF('day', a.VDATU, l.WADAT_IST), 0)), 2)         AS avg_days_late,
       ROUND(100 * AVG(CASE WHEN DATE_DIFF('day', a.VDATU, l.WADAT_IST) > 7 THEN 1 ELSE 0 END), 1) AS pct_over_7_days_late
FROM LIKP l
JOIN (SELECT DISTINCT VBELN, VGBEL FROM LIPS) lp ON lp.VBELN = l.VBELN
JOIN VBAK a  ON a.VBELN = lp.VGBEL
JOIN T001W w ON w.WERKS = l.VSTEL
GROUP BY 1
ORDER BY pct_on_time;
