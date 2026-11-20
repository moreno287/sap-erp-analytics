-- ABC classification of customers by billed revenue (A = top 80%, B = next 15%, C = last 5%).
WITH rev AS (
    SELECT KUNAG AS customer, SUM(NETWR) AS revenue FROM VBRK GROUP BY 1
),
ranked AS (
    SELECT *, SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER () AS cum_share
    FROM rev
)
SELECT CASE WHEN cum_share <= 0.80 THEN 'A' WHEN cum_share <= 0.95 THEN 'B' ELSE 'C' END AS abc_class,
       COUNT(*)                                                  AS customers,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct_customers,
       ROUND(SUM(revenue), 0)                                    AS revenue_cad,
       ROUND(100 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1)  AS pct_revenue
FROM ranked
GROUP BY 1
ORDER BY 1;
