PRAGMA foreign_keys=ON;
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sync_runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  source TEXT NOT NULL,
  products_total INTEGER NOT NULL,
  products_active INTEGER NOT NULL,
  github_products INTEGER NOT NULL,
  status TEXT NOT NULL,
  notes TEXT
);
CREATE TABLE categories (
  category_id INTEGER PRIMARY KEY,
  parent_id INTEGER NOT NULL,
  active INTEGER NOT NULL,
  level_depth INTEGER NOT NULL,
  name TEXT NOT NULL,
  link_rewrite TEXT NOT NULL,
  category_url TEXT,
  source_status TEXT NOT NULL DEFAULT 'PRESENT'
);
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY,
  entity_key TEXT NOT NULL UNIQUE,
  reference TEXT,
  name TEXT NOT NULL,
  link_rewrite TEXT,
  active INTEGER NOT NULL,
  indexed INTEGER NOT NULL,
  visibility TEXT,
  available_for_order INTEGER NOT NULL,
  show_price INTEGER NOT NULL,
  default_category_id INTEGER,
  default_category_name TEXT,
  prestashop_candidate_url TEXT,
  date_upd TEXT,
  FOREIGN KEY(default_category_id) REFERENCES categories(category_id)
);
CREATE TABLE product_categories (
  product_id INTEGER NOT NULL,
  category_id INTEGER NOT NULL,
  PRIMARY KEY(product_id,category_id),
  FOREIGN KEY(product_id) REFERENCES products(product_id),
  FOREIGN KEY(category_id) REFERENCES categories(category_id)
);
CREATE TABLE prestashop_anomalies (
  anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
  anomaly_type TEXT NOT NULL,
  object_id INTEGER,
  related_id INTEGER,
  details TEXT
);
CREATE TABLE taxonomy_products (
  product_id INTEGER PRIMARY KEY,
  macroarea TEXT,
  family TEXT,
  family_entity_key TEXT,
  canonical_url TEXT NOT NULL,
  category_current TEXT,
  seo_landing_candidate TEXT,
  classification_confidence TEXT,
  classification_status TEXT,
  FOREIGN KEY(product_id) REFERENCES products(product_id)
);
CREATE TABLE ads_blueprint (
  entity_key TEXT PRIMARY KEY,
  campaign TEXT NOT NULL,
  ad_group TEXT NOT NULL,
  intent_class TEXT NOT NULL,
  macroarea TEXT,
  family TEXT,
  theme TEXT,
  keyword_count INTEGER NOT NULL,
  landing_source TEXT,
  activation_state TEXT,
  resolved_url TEXT,
  resolution_method TEXT
);
CREATE TABLE ads_keywords (
  keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
  keyword TEXT NOT NULL,
  match_type TEXT,
  legacy_ad_group TEXT,
  intent_class TEXT NOT NULL,
  macroarea TEXT,
  family TEXT,
  theme TEXT,
  entity_key TEXT,
  historical_urls TEXT,
  normalized_urls TEXT,
  classification_confidence TEXT,
  impressions_max INTEGER,
  clicks_max INTEGER,
  conversions_max REAL
);
CREATE TABLE url_registry (
  url TEXT NOT NULL,
  source TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_key TEXT NOT NULL,
  status TEXT,
  is_current INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(url,source,entity_key)
);
CREATE TABLE family_category_candidates (
  family_entity_key TEXT NOT NULL,
  family TEXT NOT NULL,
  category_id INTEGER NOT NULL,
  category_name TEXT NOT NULL,
  category_url TEXT,
  product_count INTEGER NOT NULL,
  share REAL NOT NULL,
  is_dominant INTEGER NOT NULL,
  PRIMARY KEY(family_entity_key,category_id)
);
CREATE VIEW v_active_catalog AS
SELECT p.product_id,p.entity_key,p.reference,p.name,p.active,p.indexed,p.visibility,
       t.macroarea,t.family,t.family_entity_key,t.canonical_url,
       p.default_category_id,p.default_category_name,p.date_upd
FROM products p JOIN taxonomy_products t USING(product_id)
WHERE p.active=1;
CREATE VIEW v_ads_entities AS
SELECT a.*, COUNT(k.keyword_id) AS mapped_keywords
FROM ads_blueprint a LEFT JOIN ads_keywords k ON k.entity_key=a.entity_key
GROUP BY a.entity_key;
