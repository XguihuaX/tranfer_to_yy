PRAGMA foreign_keys = ON;
BEGIN;

CREATE TABLE order_header (
    doc_id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    business_date TEXT NOT NULL,
    total_amount INTEGER NOT NULL
);
CREATE TABLE order_line (
    doc_id TEXT NOT NULL REFERENCES order_header(doc_id),
    line_no INTEGER NOT NULL,
    material_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    line_amount INTEGER NOT NULL,
    PRIMARY KEY (doc_id, line_no)
);
CREATE TABLE receivable (
    ar_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES order_header(doc_id),
    business_date TEXT NOT NULL,
    amount INTEGER NOT NULL
);
CREATE TABLE receipt (
    receipt_id TEXT PRIMARY KEY,
    ar_id TEXT NOT NULL REFERENCES receivable(ar_id),
    business_date TEXT NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('POSTED', 'DRAFT'))
);

INSERT INTO order_header VALUES
    ('SO101', 'ORG-SH', 'C001', '2026-10-15', 10000),
    ('SO105', 'ORG-SH', 'C001', '2026-10-16', 2000);
INSERT INTO order_line VALUES
    ('SO101', 1, 'M001', 8, 1000, 8000),
    ('SO101', 2, 'M002', 1, 2000, 2000),
    ('SO105', 1, 'M002', 1, 2000, 2000);
INSERT INTO receivable VALUES
    ('AR101', 'SO101', '2026-10-15', 10000),
    ('AR102', 'SO105', '2026-10-16', 2000);
INSERT INTO receipt VALUES
    ('RC101', 'AR101', '2026-10-15', 3000, 'POSTED'),
    ('RC102', 'AR101', '2026-10-16', 1000, 'POSTED'),
    ('RC103', 'AR101', '2026-10-16', 500, 'DRAFT');

COMMIT;
