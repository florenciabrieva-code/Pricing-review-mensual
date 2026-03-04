-- title: NPS Mensual
-- section: cx
-- description: Net Promoter Score del mes actual vs anterior
-- order: 2

WITH scores AS (
  SELECT
    '{{ start_date }}' AS periodo_inicio,
    score,
    CASE
      WHEN score >= 9 THEN 'Promotor'
      WHEN score >= 7 THEN 'Neutro'
      ELSE 'Detractor'
    END AS categoria
  FROM `{{ project }}.dataset.nps_responses`
  WHERE DATE(response_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
)
SELECT
  COUNT(*) AS respuestas_totales,
  ROUND(100.0 * COUNTIF(categoria = 'Promotor') / COUNT(*), 1) AS pct_promotores,
  ROUND(100.0 * COUNTIF(categoria = 'Neutro') / COUNT(*), 1) AS pct_neutros,
  ROUND(100.0 * COUNTIF(categoria = 'Detractor') / COUNT(*), 1) AS pct_detractores,
  ROUND(
    100.0 * COUNTIF(categoria = 'Promotor') / COUNT(*) -
    100.0 * COUNTIF(categoria = 'Detractor') / COUNT(*),
    1
  ) AS nps
FROM scores
