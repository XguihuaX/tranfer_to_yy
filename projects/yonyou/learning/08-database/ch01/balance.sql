WITH paid AS (
    SELECT ar_id, SUM(amount) AS paid_amount
    FROM receipt
    WHERE status = 'POSTED'
    GROUP BY ar_id
)
SELECT a.ar_id,
       a.order_id,
       a.amount AS receivable_amount,
       COALESCE(p.paid_amount, 0) AS paid_amount,
       a.amount - COALESCE(p.paid_amount, 0) AS balance
FROM receivable AS a
JOIN order_header AS h ON h.doc_id = a.order_id
LEFT JOIN paid AS p ON p.ar_id = a.ar_id
WHERE h.org_id = 'ORG-SH' AND h.customer_id = 'C001'
ORDER BY a.ar_id;
