\echo 'Loading users...'
\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV HEADER
SELECT pg_catalog.setval(
    pg_get_serial_sequence('users','id'),
    (SELECT COALESCE(MAX(id),0) FROM users) + 1,
    false
);

\echo 'Loading products...'
\COPY Products(id, name, description, image, category, created_by) FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV HEADER
SELECT pg_catalog.setval(
    pg_get_serial_sequence('products','id'),
    (SELECT COALESCE(MAX(id),0) FROM products) + 1,
    false
);


\echo 'Loading inventory...'
\COPY Inventory FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV HEADER


\echo 'Loading carts...'
\COPY Cart FROM 'Carts.csv' WITH DELIMITER ',' NULL '' CSV HEADER


\echo 'Loading purchases...'
\COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV HEADER
SELECT pg_catalog.setval(
    pg_get_serial_sequence('purchases','purchase_id'),
    (SELECT COALESCE(MAX(purchase_id),0) FROM purchases) + 1,
    false
);

\echo 'Loading Ledger...'
\COPY Ledger FROM 'Order_items.csv' WITH DELIMITER ',' NULL '' CSV HEADER

\echo 'All CSV imports finished.'