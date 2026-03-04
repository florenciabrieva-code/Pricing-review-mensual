# Monthly Review

Repositorio para la review mensual de **Negocio · Producto · CX**.

## ¿Cómo funciona?

1. El equipo agrega o edita queries `.sql` en la carpeta `queries/`
2. Cada mes, se dispara manualmente el workflow de GitHub Actions con el año y mes deseado
3. El workflow conecta a BigQuery, corre todas las queries y genera un HTML
4. El reporte queda publicado en GitHub Pages automáticamente

## Estructura

```
monthly-review/
├── .github/workflows/
│   └── generate_report.yml   # Workflow manual: inputs year + month
├── queries/
│   ├── README.md              # Instrucciones para agregar queries
│   ├── business/              # KPIs de negocio
│   ├── product/               # Métricas de producto
│   └── cx/                    # Métricas de CX
├── scripts/
│   ├── run_report.py          # Conecta a BQ, genera HTML
│   ├── update_index.py        # Regenera el index con todos los reportes
│   └── requirements.txt
├── templates/
│   └── report.html.j2         # Template Jinja2 del reporte
├── reports/                   # HTMLs generados (uno por mes)
│   └── 2026-03/index.html
└── index.html                 # Página principal con todos los reportes
```

## Generar un reporte

### Con el script (recomendado)

Desde la carpeta del repo, correr en CMD o PowerShell:

```
generar_reporte.bat 2026 3
```

Esto:
1. Corre las queries en BigQuery (usando tus credenciales de gcloud)
2. Genera el HTML en `reports/2026-03/`
3. Actualiza el `index.html`
4. Commitea y pushea a GitHub
5. GitHub Actions despliega automáticamente a GitHub Pages

El reporte queda en: `https://florenciabrieva-code.github.io/Pricing-review-mensual/reports/2026-03/`

### Manualmente (paso a paso)

```bash
pip install -r scripts/requirements.txt
python scripts/run_report.py --year 2026 --month 3
python scripts/update_index.py
git add reports/ index.html
git commit -m "report: reporte 2026-03"
git push
```

### Dry run (probar template sin ejecutar queries)

```bash
python scripts/run_report.py --year 2026 --month 3 --dry-run
```

## Agregar una nueva query

Ver `queries/README.md` para instrucciones detalladas.

Resumen rápido: crear un `.sql` en la carpeta correspondiente con metadatos:

```sql
-- title: Nombre visible en el reporte
-- section: business | product | cx
-- description: Qué muestra esta query
-- order: 1

SELECT ...
FROM `{{ project }}.dataset.tabla`
WHERE DATE(col) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
```

## Configuración de GitHub

### GitHub Pages (Settings → Pages)

- **Source**: GitHub Actions
- Se despliega automáticamente cada vez que se pushean cambios en `reports/` o `index.html`

### Requisito local

Tener autenticación de gcloud activa:
```
gcloud auth application-default login
```

## Parámetros disponibles en queries

| Placeholder | Ejemplo | Descripción |
|-------------|---------|-------------|
| `{{ year }}` | `2026` | Año del reporte |
| `{{ month }}` | `03` | Mes (con cero) |
| `{{ start_date }}` | `2026-03-01` | Primer día del mes |
| `{{ end_date }}` | `2026-03-31` | Último día del mes |
| `{{ prev_start_date }}` | `2026-02-01` | Primer día del mes anterior |
| `{{ prev_end_date }}` | `2026-02-28` | Último día del mes anterior |
| `{{ project }}` | `meli-bi-data` | Proyecto BQ |
