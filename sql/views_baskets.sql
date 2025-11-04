-- Daily prices for a basket
CREATE OR REPLACE VIEW v_basket_prices AS
SELECT
  bm.slug,
  p.dt,
  AVG(p.adj_close) AS avg_adj_close
FROM basket_members bm
JOIN prices_daily p USING (ticker)
GROUP BY bm.slug, p.dt;

-- Daily equal-weight r1d per basket
CREATE OR REPLACE VIEW v_basket_returns AS
WITH r AS (
  SELECT
    p.ticker, bm.slug, p.dt,
    p.adj_close / LAG(p.adj_close) OVER (PARTITION BY p.ticker ORDER BY p.dt) - 1 AS r1d
  FROM prices_daily p
  JOIN basket_members bm USING (ticker)
)
SELECT slug, dt, AVG(r1d) AS ew_r1d
FROM r
WHERE r1d IS NOT NULL
GROUP BY slug, dt;
