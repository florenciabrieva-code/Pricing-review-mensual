# Cómo agregar queries

## Estructura de carpetas
```
queries/
├── business/   → KPIs de negocio (revenue, GMV, transacciones)
├── product/    → Métricas de producto (uso, retención, funnel)
└── cx/         → Métricas de CX (tickets, NPS, satisfacción)
```

## Formato de un archivo .sql

Cada `.sql` debe comenzar con un bloque de metadatos en comentarios:

```sql
-- title: Nombre legible de la query
-- section: business | product | cx
-- description: Explicación corta de qué muestra
-- order: 1   (número para ordenar dentro de la sección)

SELECT ...
```

## Parámetros disponibles en las queries

| Placeholder          | Ejemplo           | Descripción                        |
|----------------------|-------------------|------------------------------------|
| `{{ year }}`         | `2026`            | Año del reporte                    |
| `{{ month }}`        | `03`              | Mes del reporte (con cero)         |
| `{{ start_date }}`   | `2026-03-01`      | Primer día del mes                 |
| `{{ end_date }}`     | `2026-03-31`      | Último día del mes                 |
| `{{ prev_start_date }}` | `2026-02-01`  | Primer día del mes anterior        |
| `{{ prev_end_date }}` | `2026-02-28`    | Último día del mes anterior        |
| `{{ project }}`      | `meli-bi-data`    | Proyecto de BigQuery               |

## Ejemplo

```sql
-- title: Transacciones por día
-- section: business
-- description: Volumen diario de transacciones del mes
-- order: 2

SELECT
  DATE(created_at) AS fecha,
  COUNT(*) AS transacciones,
  SUM(amount) AS monto_total
FROM `{{ project }}.dataset.transactions`
WHERE DATE(created_at) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY 1
ORDER BY 1
```

## Reglas
- Un archivo `.sql` = una tabla en el reporte
- Nombres de archivo en `snake_case`
- No uses `;` al final de la query
