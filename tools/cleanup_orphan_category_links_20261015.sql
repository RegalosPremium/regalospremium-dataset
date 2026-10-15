-- Repair completed by a guarded MariaDB transaction on 2026-10-15.
-- Evidence: reports/prestashop/orphan_repair_20261015.json.
-- This file remains a ROLLBACK-only rehearsal for review; rerunning should find zero rows.
-- Replace ps_ only if the production table prefix differs.
-- Save the first SELECT output with id_category, id_product and position before applying.
START TRANSACTION;
SELECT cp.* FROM ps_category_product cp
LEFT JOIN ps_product p ON p.id_product=cp.id_product
WHERE p.id_product IS NULL AND
 ((cp.id_category=2 AND cp.id_product IN (805,844,845,846,847,848,849,850,851))
 OR (cp.id_category=71 AND cp.id_product=855));
DELETE cp FROM ps_category_product cp
LEFT JOIN ps_product p ON p.id_product=cp.id_product
WHERE p.id_product IS NULL AND
 ((cp.id_category=2 AND cp.id_product IN (805,844,845,846,847,848,849,850,851))
 OR (cp.id_category=71 AND cp.id_product=855));
SELECT ROW_COUNT() AS removed_links;
-- Rehearsal default: replace ROLLBACK with COMMIT only after checking exactly 10 rows.
ROLLBACK;
