-- How long do purchase requisitions (EBAN) wait before becoming a purchase order (EKKO)? By purchasing group.
SELECT e.EKGRP                                                        AS purchasing_group,
       COUNT(*)                                                       AS requisitions,
       ROUND(AVG(DATE_DIFF('day', e.BADAT, k.BEDAT)), 1)              AS avg_days_pr_to_po,
       QUANTILE_CONT(DATE_DIFF('day', e.BADAT, k.BEDAT), 0.9)         AS p90_days,
       ROUND(100 * AVG(CASE WHEN DATE_DIFF('day', e.BADAT, k.BEDAT) > 5 THEN 1 ELSE 0 END), 1) AS pct_over_5_days
FROM EBAN e
JOIN EKKO k ON k.EBELN = e.EBELN
GROUP BY 1
ORDER BY 1;
