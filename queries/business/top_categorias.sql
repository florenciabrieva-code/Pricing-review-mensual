-- title: Top 10 Categorías por Volumen
-- section: business
-- description: Categorías con mayor volumen de transacciones en el mes
-- order: 2

SELECT
  category,
  COUNT(*) AS transacciones,
  SUM(amount) AS revenue_total,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_transacciones
FROM `{{ project }}.dataset.transactions`
WHERE DATE(created_at) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY 1
ORDER BY revenue_total DESC
LIMIT 10
