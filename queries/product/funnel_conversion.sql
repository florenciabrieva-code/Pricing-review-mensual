-- title: Funnel de Conversión
-- section: product
-- description: Conversión por etapa del funnel en el mes
-- order: 2

SELECT
  step,
  COUNT(DISTINCT user_id) AS usuarios,
  ROUND(
    100.0 * COUNT(DISTINCT user_id) / FIRST_VALUE(COUNT(DISTINCT user_id)) OVER (ORDER BY step_order),
    2
  ) AS conversion_vs_inicio_pct
FROM `{{ project }}.dataset.funnel_events`
WHERE DATE(event_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY step, step_order
ORDER BY step_order
