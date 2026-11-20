-- On-time shipping % by month and plant (for the trend chart).
SELECT DATE_TRUNC('month', a.ERDAT) AS month,
       l.VSTEL                      AS plant,
       ROUND(100 * AVG(CASE WHEN l.WADAT_IST <= a.VDATU THEN 1 ELSE 0 END), 1) AS pct_on_time
FROM LIKP l
JOIN (SELECT DISTINCT VBELN, VGBEL FROM LIPS) lp ON lp.VBELN = l.VBELN
JOIN VBAK a ON a.VBELN = lp.VGBEL
GROUP BY 1, 2
ORDER BY 1, 2;
