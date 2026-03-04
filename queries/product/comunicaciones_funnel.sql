-- title: Comunicaciones - Funnel por Campana
-- section: product
-- description: Funnel enviado/entregado/abierto y conversion a Costos/Pricing el mismo dia que apertura
-- order: 5

-- Nota: ajustar campo de fecha en MELIDATA.TRACKS si difiere (ds vs DS_DT)
--       y verificar que USER_ID sea el mismo identificador en ambas tablas.

WITH

-- ── Mapeo de campaign_id a nombre de flow, pais y canal ──────────────────────
campanas AS (
  SELECT campaign_id, nombre, pais, canal FROM (
    -- MLB ─────────────────────────────────────────────────────────────────────
    SELECT 988190  AS campaign_id, 'PROMO_MLB_ONBOARDING'  AS nombre, 'MLB' AS pais, 'PUSH' AS canal UNION ALL
    SELECT 987802,                 'PROMO_MLB_ONBOARDING',             'MLB',         'MAIL'         UNION ALL
    SELECT 1166990,                'PROMO_MLB_HALF_TIME',              'MLB',         'PUSH'         UNION ALL
    SELECT 988196,                 'END_PROMO_MLB',                    'MLB',         'PUSH'         UNION ALL
    SELECT 983401,                 'END_PROMO_MLB',                    'MLB',         'MAIL'         UNION ALL
    SELECT 976110,                 'PROMO_MLB_END_TPV',                'MLB',         'PUSH'         UNION ALL
    SELECT 976101,                 'PROMO_MLB_END_TPV',                'MLB',         'MAIL'         UNION ALL
    SELECT 1030649,                'SCALE_MLB_ONBOARDING',             'MLB',         'PUSH'         UNION ALL
    SELECT 1030646,                'SCALE_MLB_ONBOARDING',             'MLB',         'MAIL'         UNION ALL
    SELECT 1199228,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1185180,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1185179,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1185181,                'RECALC_SCALE_MLB',                 'MLB',         'MAIL'         UNION ALL
    SELECT 1185177,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1185176,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1185174,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1185173,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1196773,                'RECALC_SCALE_MLB',                 'MLB',         'PUSH'         UNION ALL
    SELECT 1185172,                'RECALC_SCALE_MLB',                 'MLB',         'MAIL'         UNION ALL
    SELECT 1185171,                'RECALC_SCALE_MLB',                 'MLB',         'MAIL'         UNION ALL
    SELECT 1185170,                'RECALC_SCALE_MLB',                 'MLB',         'MAIL'         UNION ALL
    -- MLA ─────────────────────────────────────────────────────────────────────
    SELECT 1168551,                'SCALE_MLA_ONBOARDING',             'MLA',         'PUSH'         UNION ALL
    SELECT 1168553,                'SCALE_MLA_ONBOARDING',             'MLA',         'MAIL'         UNION ALL
    SELECT 1189951,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    SELECT 1189949,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    SELECT 1189948,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    SELECT 1190672,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    SELECT 1190674,                'RECALC_SCALE_MLA',                 'MLA',         'MAIL'         UNION ALL
    SELECT 1190668,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    SELECT 1190669,                'RECALC_SCALE_MLA',                 'MLA',         'MAIL'         UNION ALL
    SELECT 1189954,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    SELECT 1189956,                'RECALC_SCALE_MLA',                 'MLA',         'MAIL'         UNION ALL
    SELECT 1190659,                'RECALC_SCALE_MLA',                 'MLA',         'MAIL'         UNION ALL
    SELECT 1189945,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    SELECT 1189946,                'RECALC_SCALE_MLA',                 'MLA',         'PUSH'         UNION ALL
    -- MLM ─────────────────────────────────────────────────────────────────────
    SELECT 1204940,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1204936,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1204652,                'RECALC_SCALE_MLM',                 'MLM',         'MAIL'         UNION ALL
    SELECT 1204647,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1204648,                'RECALC_SCALE_MLM',                 'MLM',         'MAIL'         UNION ALL
    SELECT 1204645,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1204937,                'RECALC_SCALE_MLM',                 'MLM',         'MAIL'         UNION ALL
    SELECT 1205408,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1205412,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1205215,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1205392,                'RECALC_SCALE_MLM',                 'MLM',         'PUSH'         UNION ALL
    SELECT 1188379,                'SCALE_MLM_ONBOARDING',             'MLM',         'PUSH'         UNION ALL
    SELECT 1186254,                'SCALE_MLM_ONBOARDING',             'MLM',         'MAIL'         UNION ALL
    -- MLC ─────────────────────────────────────────────────────────────────────
    SELECT 1188382,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1189184,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1189182,                'RECALC_SCALE_MLC',                 'MLC',         'MAIL'         UNION ALL
    SELECT 1188757,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1189053,                'RECALC_SCALE_MLC',                 'MLC',         'MAIL'         UNION ALL
    SELECT 1188380,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1188381,                'RECALC_SCALE_MLC',                 'MLC',         'MAIL'         UNION ALL
    SELECT 1188386,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1188385,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1188383,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1188384,                'RECALC_SCALE_MLC',                 'MLC',         'PUSH'         UNION ALL
    SELECT 1166641,                'SCALE_MLC_ONBOARDING',             'MLC',         'PUSH'         UNION ALL
    SELECT 1166249,                'SCALE_MLC_ONBOARDING',             'MLC',         'MAIL'
  )
),

-- ── Eventos Mercurio en el periodo ────────────────────────────────────────────
mercurio AS (
  SELECT
    CAMPAIGN_ID   AS campaign_id,
    USER_ID,
    DS_DT         AS event_date,
    EVENT_TYPE
  FROM `meli-bi-data.WHOWNER.BT_OC_MERCURIO_EVENTS`
  WHERE DS_DT BETWEEN '{{ start_date }}' AND '{{ end_date }}'
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

-- ── Funnel agregado por campana + pais + canal ────────────────────────────────
funnel AS (
  SELECT
    c.nombre,
    c.pais,
    c.canal,
    -- PUSH: create -> shown -> open  |  MAIL: processed -> delivered -> open
    COUNT(DISTINCT CASE WHEN m.EVENT_TYPE IN ('create','processed') THEN m.USER_ID END) AS enviados,
    COUNT(DISTINCT CASE WHEN m.EVENT_TYPE IN ('shown','delivered')  THEN m.USER_ID END) AS entregados,
    COUNT(DISTINCT CASE WHEN m.EVENT_TYPE = 'open'                  THEN m.USER_ID END) AS abiertos
  FROM campanas c
  LEFT JOIN mercurio m ON m.campaign_id = c.campaign_id
  GROUP BY c.nombre, c.pais, c.canal
),

-- ── Usuarios que abrieron (con fecha para join mismo-dia) ─────────────────────
aperturas AS (
  SELECT DISTINCT
    c.nombre   AS campana,
    c.pais,
    c.canal,
    m.USER_ID,
    m.event_date
  FROM campanas c
  JOIN mercurio m ON m.campaign_id = c.campaign_id AND m.EVENT_TYPE = 'open'
),

-- ── Visitas a seccion Costos ──────────────────────────────────────────────────
visitas_costos AS (
  SELECT DISTINCT usr.user_id, ds AS visit_date
  FROM `meli-bi-data.MELIDATA.TRACKS`
  WHERE ds BETWEEN '{{ start_date }}' AND '{{ end_date }}'
    AND path = '/cost_section/success'
),

-- ── Visitas a seccion Pricing ─────────────────────────────────────────────────
visitas_pricing AS (
  SELECT DISTINCT usr.user_id, ds AS visit_date
  FROM `meli-bi-data.MELIDATA.TRACKS`
  WHERE ds BETWEEN '{{ start_date }}' AND '{{ end_date }}'
    AND JSON_EXTRACT_SCALAR(event_data, '$.step') = '101'
    AND path = '/pricing_models/scale_legacy/flow'
),

-- ── Conversiones: abrio la comunicacion Y visito seccion el mismo dia ─────────
conversiones AS (
  SELECT
    a.campana,
    a.pais,
    a.canal,
    COUNT(DISTINCT CASE WHEN vc.user_id IS NOT NULL THEN a.USER_ID END) AS conv_costos,
    COUNT(DISTINCT CASE WHEN vp.user_id IS NOT NULL THEN a.USER_ID END) AS conv_pricing
  FROM aperturas a
  LEFT JOIN visitas_costos  vc ON vc.user_id = a.USER_ID AND vc.visit_date = a.event_date
  LEFT JOIN visitas_pricing vp ON vp.user_id = a.USER_ID AND vp.visit_date = a.event_date
  GROUP BY a.campana, a.pais, a.canal
)

-- ── Resultado final ───────────────────────────────────────────────────────────
SELECT
  f.pais                                                                             AS Pais,
  f.canal                                                                            AS Canal,
  f.nombre                                                                           AS Campana,
  f.enviados                                                                         AS Enviados,
  f.entregados                                                                       AS Entregados,
  f.abiertos                                                                         AS Abiertos,
  ROUND(SAFE_DIVIDE(f.abiertos, f.entregados) * 100, 1)                             AS Pct_Open_Rate,
  COALESCE(co.conv_costos,  0)                                                       AS Conv_Costos,
  COALESCE(co.conv_pricing, 0)                                                       AS Conv_Pricing,
  ROUND(
    SAFE_DIVIDE(COALESCE(co.conv_costos,0) + COALESCE(co.conv_pricing,0), f.abiertos) * 100,
    1
  )                                                                                  AS Pct_Conv_Seccion
FROM funnel f
LEFT JOIN conversiones co
  ON co.campana = f.nombre
  AND co.pais   = f.pais
  AND co.canal  = f.canal
WHERE f.enviados > 0 OR f.entregados > 0 OR f.abiertos > 0
ORDER BY f.pais, f.canal, f.nombre