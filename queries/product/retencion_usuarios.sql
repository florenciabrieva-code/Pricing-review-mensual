-- title: Retención de Usuarios
-- section: product
-- description: Usuarios activos en el mes actual vs mes anterior
-- order: 1

WITH mes_actual AS (
  SELECT DISTINCT user_id
  FROM `{{ project }}.dataset.events`
  WHERE DATE(event_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
),
mes_anterior AS (
  SELECT DISTINCT user_id
  FROM `{{ project }}.dataset.events`
  WHERE DATE(event_date) BETWEEN '{{ prev_start_date }}' AND '{{ prev_end_date }}'
)
SELECT
  COUNT(DISTINCT ma.user_id) AS usuarios_activos_mes,
  COUNT(DISTINCT mant.user_id) AS usuarios_mes_anterior,
  COUNT(DISTINCT CASE WHEN ma.user_id IS NOT NULL AND mant.user_id IS NOT NULL THEN ma.user_id END) AS retenidos,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN ma.user_id IS NOT NULL AND mant.user_id IS NOT NULL THEN ma.user_id END)
    / NULLIF(COUNT(DISTINCT mant.user_id), 0),
    2
  ) AS tasa_retencion_pct
FROM mes_actual ma
FULL OUTER JOIN mes_anterior mant USING (user_id)
