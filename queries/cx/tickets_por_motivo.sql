-- title: Tickets por Motivo
-- section: cx
-- description: Distribución de tickets de soporte por motivo en el mes
-- order: 1

SELECT
  motivo,
  COUNT(*) AS tickets,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_total,
  ROUND(AVG(resolution_time_hours), 1) AS tiempo_resolucion_promedio_hs
FROM `{{ project }}.dataset.support_tickets`
WHERE DATE(created_at) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY 1
ORDER BY tickets DESC
