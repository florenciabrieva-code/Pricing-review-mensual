-- title: Comunicaciones - Tendencia 6 Meses
-- section: product
-- description: Evolucion mensual de enviados, abiertos y tasa de apertura por pais y canal (ultimos 6 meses)
-- order: 6

WITH

-- ── Mapeo de campaign_id a pais y canal ──────────────────────────────────────
campanas AS (
  SELECT campaign_id, pais, canal FROM (
    -- MLB ─────────────────────────────────────────────────────────────────────
    SELECT 988190  AS campaign_id, 'MLB' AS pais, 'PUSH' AS canal UNION ALL
    SELECT 987802,                 'MLB',          'MAIL'         UNION ALL
    SELECT 1166990,                'MLB',          'PUSH'         UNION ALL
    SELECT 988196,                 'MLB',          'PUSH'         UNION ALL
    SELECT 983401,                 'MLB',          'MAIL'         UNION ALL
    SELECT 976110,                 'MLB',          'PUSH'         UNION ALL
    SELECT 976101,                 'MLB',          'MAIL'         UNION ALL
    SELECT 1030649,                'MLB',          'PUSH'         UNION ALL
    SELECT 1030646,                'MLB',          'MAIL'         UNION ALL
    SELECT 1199228,                'MLB',          'PUSH'         UNION ALL
    SELECT 1185180,                'MLB',          'PUSH'         UNION ALL
    SELECT 1185179,                'MLB',          'PUSH'         UNION ALL
    SELECT 1185181,                'MLB',          'MAIL'         UNION ALL
    SELECT 1185177,                'MLB',          'PUSH'         UNION ALL
    SELECT 1185176,                'MLB',          'PUSH'         UNION ALL
    SELECT 1185174,                'MLB',          'PUSH'         UNION ALL
    SELECT 1185173,                'MLB',          'PUSH'         UNION ALL
    SELECT 1196773,                'MLB',          'PUSH'         UNION ALL
    SELECT 1185172,                'MLB',          'MAIL'         UNION ALL
    SELECT 1185171,                'MLB',          'MAIL'         UNION ALL
    SELECT 1185170,                'MLB',          'MAIL'         UNION ALL
    -- MLA ─────────────────────────────────────────────────────────────────────
    SELECT 1168551,                'MLA',          'PUSH'         UNION ALL
    SELECT 1168553,                'MLA',          'MAIL'         UNION ALL
    SELECT 1189951,                'MLA',          'PUSH'         UNION ALL
    SELECT 1189949,                'MLA',          'PUSH'         UNION ALL
    SELECT 1189948,                'MLA',          'PUSH'         UNION ALL
    SELECT 1190672,                'MLA',          'PUSH'         UNION ALL
    SELECT 1190674,                'MLA',          'MAIL'         UNION ALL
    SELECT 1190668,                'MLA',          'PUSH'         UNION ALL
    SELECT 1190669,                'MLA',          'MAIL'         UNION ALL
    SELECT 1189954,                'MLA',          'PUSH'         UNION ALL
    SELECT 1189956,                'MLA',          'MAIL'         UNION ALL
    SELECT 1190659,                'MLA',          'MAIL'         UNION ALL
    SELECT 1189945,                'MLA',          'PUSH'         UNION ALL
    SELECT 1189946,                'MLA',          'PUSH'         UNION ALL
    -- MLM ─────────────────────────────────────────────────────────────────────
    SELECT 1204940,                'MLM',          'PUSH'         UNION ALL
    SELECT 1204936,                'MLM',          'PUSH'         UNION ALL
    SELECT 1204652,                'MLM',          'MAIL'         UNION ALL
    SELECT 1204647,                'MLM',          'PUSH'         UNION ALL
    SELECT 1204648,                'MLM',          'MAIL'         UNION ALL
    SELECT 1204645,                'MLM',          'PUSH'         UNION ALL
    SELECT 1204937,                'MLM',          'MAIL'         UNION ALL
    SELECT 1205408,                'MLM',          'PUSH'         UNION ALL
    SELECT 1205412,                'MLM',          'PUSH'         UNION ALL
    SELECT 1205215,                'MLM',          'PUSH'         UNION ALL
    SELECT 1205392,                'MLM',          'PUSH'         UNION ALL
    SELECT 1188379,                'MLM',          'PUSH'         UNION ALL
    SELECT 1186254,                'MLM',          'MAIL'         UNION ALL
    -- MLC ─────────────────────────────────────────────────────────────────────
    SELECT 1188382,                'MLC',          'PUSH'         UNION ALL
    SELECT 1189184,                'MLC',          'PUSH'         UNION ALL
    SELECT 1189182,                'MLC',          'MAIL'         UNION ALL
    SELECT 1188757,                'MLC',          'PUSH'         UNION ALL
    SELECT 1189053,                'MLC',          'MAIL'         UNION ALL
    SELECT 1188380,                'MLC',          'PUSH'         UNION ALL
    SELECT 1188381,                'MLC',          'MAIL'         UNION ALL
    SELECT 1188386,                'MLC',          'PUSH'         UNION ALL
    SELECT 1188385,                'MLC',          'PUSH'         UNION ALL
    SELECT 1188383,                'MLC',          'PUSH'         UNION ALL
    SELECT 1188384,                'MLC',          'PUSH'         UNION ALL
    SELECT 1166641,                'MLC',          'PUSH'         UNION ALL
    SELECT 1166249,                'MLC',          'MAIL'
  )
),

-- ── Eventos Mercurio: ultimos 6 meses hasta el fin del periodo ────────────────
mercurio AS (
  SELECT
    CAMPAIGN_ID  AS campaign_id,
    USER_ID,
    DS_DT        AS event_date,
    EVENT_TYPE
  FROM `meli-bi-data.WHOWNER.BT_OC_MERCURIO_EVENTS`
  WHERE DS_DT >= DATE_SUB(DATE('{{ end_date }}'), INTERVAL 5 MONTH)
    AND DS_DT <= DATE('{{ end_date }}')
    AND CAMPAIGN_ID IN (
      988190,987802,1166990,988196,983401,976110,976101,1030649,1030646,
      1199228,1185180,1185179,1185181,1185177,1185176,1185174,1185173,
      1196773,1185172,1185171,1185170,
      1168551,1168553,1189951,1189949,1189948,1190672,1190674,1190668,
      1190669,1189954,1189956,1190659,1189945,1189946,
      1204940,1204936,1204652,1204647,1204648,1204645,1204937,1205408,
      1205412,1205215,1205392,1188379,1186254,
      1188382,1189184,1189182,1188757,1189053,1188380,1188381,1188386,
      1188385,1188383,1188384,1166641,1166249
    )
),

-- ── Agrupado por mes, pais y canal ────────────────────────────────────────────
mensual AS (
  SELECT
    FORMAT_DATE('%Y-%m', m.event_date)                                              AS mes,
    c.pais,
    c.canal,
    COUNT(DISTINCT CASE WHEN m.EVENT_TYPE IN ('create','processed') THEN m.USER_ID END) AS enviados,
    COUNT(DISTINCT CASE WHEN m.EVENT_TYPE IN ('shown','delivered')  THEN m.USER_ID END) AS entregados,
    COUNT(DISTINCT CASE WHEN m.EVENT_TYPE = 'open'                  THEN m.USER_ID END) AS abiertos
  FROM campanas c
  LEFT JOIN mercurio m ON m.campaign_id = c.campaign_id
  GROUP BY 1, 2, 3
)

SELECT
  mes        AS Mes,
  pais       AS Pais,
  canal      AS Canal,
  enviados   AS Enviados,
  entregados AS Entregados,
  abiertos   AS Abiertos,
  ROUND(SAFE_DIVIDE(abiertos, entregados) * 100, 1) AS Pct_Open_Rate
FROM mensual
WHERE enviados > 0 OR entregados > 0 OR abiertos > 0
ORDER BY mes, pais, canal
