-- Three-way match: purchase order (EKPO) vs goods receipt (MSEG) vs vendor invoice (RSEG).
-- Flags invoices whose unit price is >1% above the PO price, or whose quantity is above what was received.
WITH m AS (
    SELECT r.BELNR, i.LIFNR, i.BLDAT, r.EBELN, r.EBELP,
           p.NETPR                        AS po_price,
           r.WRBTR / r.MENGE              AS invoice_price,
           g.MENGE                        AS gr_qty,
           r.MENGE                        AS invoice_qty,
           r.WRBTR                        AS invoice_amount,
           g.MENGE * p.NETPR              AS expected_amount
    FROM RSEG r
    JOIN RBKP i ON i.BELNR = r.BELNR
    JOIN EKPO p ON p.EBELN = r.EBELN AND p.EBELP = r.EBELP
    JOIN MSEG g ON g.EBELN = r.EBELN AND g.EBELP = r.EBELP AND g.BWART = '101'
)
SELECT CASE
         WHEN invoice_price > po_price * 1.01 AND invoice_qty > gr_qty THEN 'Price and quantity mismatch'
         WHEN invoice_price > po_price * 1.01                       THEN 'Price above PO (>1%)'
         WHEN invoice_qty > gr_qty                                  THEN 'Billed more than received'
         ELSE                                                            'Matched'
       END                                                        AS match_result,
       COUNT(*)                                                   AS invoices,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)           AS pct_invoices,
       ROUND(SUM(invoice_amount), 0)                              AS invoiced_cad,
       ROUND(SUM(invoice_amount - expected_amount), 0)            AS overbilled_cad
FROM m
GROUP BY 1
ORDER BY invoices DESC;
