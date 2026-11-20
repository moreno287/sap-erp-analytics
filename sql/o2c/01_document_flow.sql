-- Document flow funnel: sales order -> delivery -> billing -> payment (like transaction VA03 "Document flow").
WITH so AS (SELECT VBELN FROM VBAK),
cancelled AS (SELECT DISTINCT VBELN FROM VBAP WHERE ABGRU IS NOT NULL),
delivered AS (SELECT DISTINCT VGBEL AS VBELN FROM LIPS),
billed AS (SELECT DISTINCT AUBEL AS VBELN FROM VBRP),
paid AS (SELECT DISTINCT p.AUBEL AS VBELN FROM VBRP p JOIN BSAD b ON b.VBELN = p.VBELN)
SELECT '1. Sales orders (VBAK)'      AS step, COUNT(*) AS documents FROM so
UNION ALL SELECT '2. Rejected / cancelled', COUNT(*) FROM cancelled
UNION ALL SELECT '3. Delivered (LIKP/LIPS)', COUNT(*) FROM delivered
UNION ALL SELECT '4. Billed (VBRK/VBRP)',    COUNT(*) FROM billed
UNION ALL SELECT '5. Paid & cleared (BSAD)', COUNT(*) FROM paid
ORDER BY step;
