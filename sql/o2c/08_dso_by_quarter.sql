-- Days Sales Outstanding at each quarter end = open AR / gross billed in the last 90 days * 90.
-- Open AR at a date = items posted on or before it and not cleared by it (BSAD cleared later + BSID still open).
WITH all_items AS (
    SELECT BUDAT, DMBTR, AUGDT FROM BSAD
    UNION ALL
    SELECT BUDAT, DMBTR, NULL FROM BSID
),
quarter_ends AS (
    SELECT (DATE_TRUNC('quarter', d) + INTERVAL 3 MONTH - INTERVAL 1 DAY)::DATE AS q_end
    FROM generate_series(DATE '2024-04-01', DATE '2026-06-30', INTERVAL 3 MONTH) g(d)
)
SELECT q.q_end                                                                        AS quarter_end,
       ROUND(SUM(CASE WHEN BUDAT <= q.q_end AND (AUGDT IS NULL OR AUGDT > q.q_end) THEN DMBTR END), 0) AS open_ar_cad,
       ROUND(SUM(CASE WHEN BUDAT > q.q_end - INTERVAL 90 DAY AND BUDAT <= q.q_end THEN DMBTR END), 0)  AS billed_last_90d_cad,
       ROUND(90 * SUM(CASE WHEN BUDAT <= q.q_end AND (AUGDT IS NULL OR AUGDT > q.q_end) THEN DMBTR END)
                / SUM(CASE WHEN BUDAT > q.q_end - INTERVAL 90 DAY AND BUDAT <= q.q_end THEN DMBTR END), 1) AS dso_days
FROM quarter_ends q CROSS JOIN all_items
GROUP BY 1
ORDER BY 1;
