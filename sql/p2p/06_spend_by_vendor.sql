-- Spend concentration: invoiced spend by vendor, cumulative share (Pareto).
WITH s AS (
    SELECT i.LIFNR, v.NAME1, v.LAND1, SUM(i.RMWWR) AS spend
    FROM RBKP i JOIN LFA1 v USING (LIFNR)
    GROUP BY ALL
)
SELECT ROW_NUMBER() OVER (ORDER BY spend DESC)                          AS rank,
       LIFNR AS vendor, NAME1 AS name, LAND1 AS country,
       ROUND(spend, 0)                                                   AS spend_cad,
       ROUND(100 * spend / SUM(spend) OVER (), 1)                        AS pct_spend,
       ROUND(100 * SUM(spend) OVER (ORDER BY spend DESC) / SUM(spend) OVER (), 1) AS cum_pct_spend
FROM s
ORDER BY spend DESC;
