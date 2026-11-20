-- "Maverick" buying: the vendor's invoice is dated before the PO was created, so the PO was raised after the fact.
-- Also counts PO items with no purchase requisition.
WITH po_items AS (
    SELECT p.EBELN, p.EBELP, p.NETWR, k.BEDAT, k.EKGRP,
           MIN(i.BLDAT) AS first_invoice_date,
           p.BANFN
    FROM EKPO p
    JOIN EKKO k ON k.EBELN = p.EBELN
    LEFT JOIN RSEG r ON r.EBELN = p.EBELN AND r.EBELP = p.EBELP
    LEFT JOIN RBKP i ON i.BELNR = r.BELNR
    GROUP BY ALL
)
SELECT EKGRP                                                                          AS purchasing_group,
       COUNT(*)                                                                       AS po_items,
       ROUND(SUM(NETWR), 0)                                                           AS po_value_cad,
       SUM(CASE WHEN first_invoice_date < BEDAT THEN 1 ELSE 0 END)                    AS after_the_fact_pos,
       ROUND(100 * SUM(CASE WHEN first_invoice_date < BEDAT THEN NETWR ELSE 0 END) / SUM(NETWR), 1) AS pct_value_after_the_fact,
       ROUND(100 * AVG(CASE WHEN BANFN IS NULL OR BANFN = '' THEN 1 ELSE 0 END), 1)    AS pct_without_requisition
FROM po_items
GROUP BY ROLLUP (EKGRP)
ORDER BY EKGRP NULLS LAST;
