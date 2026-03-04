-- title: Revenue MoM
-- section: business
-- description: Comparativo de revenue entre el mes actual y el anterior
-- order: 1

SELECT
  'Mes actual' AS periodo,
  '{{ start_date }}' AS fecha_inicio,
  '{{ end_date }}' AS fecha_fin,
  -- Reemplazar con las columnas reales del dataset
  COUNT(*) AS transacciones,
  SUM(amount) AS revenue_total,
  AVG(amount) AS ticket_promedio
FROM `{{ project }}.dataset.transactions`
WHERE DATE(created_at) BETWEEN '{{ start_date }}' AND '{{ end_date }}'

UNION ALL

SELECT
  'Mes anterior' AS periodo,
  '{{ prev_start_date }}' AS fecha_inicio,
  '{{ prev_end_date }}' AS fecha_fin,
  COUNT(*) AS transacciones,
  SUM(amount) AS revenue_total,
  AVG(amount) AS ticket_promedio
FROM `{{ project }}.dataset.transactions`
WHERE DATE(created_at) BETWEEN '{{ prev_start_date }}' AND '{{ prev_end_date }}'
