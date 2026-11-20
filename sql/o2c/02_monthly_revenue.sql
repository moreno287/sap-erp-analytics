-- Billed net revenue by month and material group (from billing documents).
SELECT DATE_TRUNC('month', k.FKDAT)        AS month,
       ROUND(SUM(p.NETWR), 0)               AS net_revenue_cad,
       COUNT(DISTINCT k.VBELN)              AS invoices,
       COUNT(DISTINCT k.KUNAG)              AS active_customers
FROM VBRK k
JOIN VBRP p ON p.VBELN = k.VBELN
GROUP BY 1
ORDER BY 1;
