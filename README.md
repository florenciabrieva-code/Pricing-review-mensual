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

### Desde GitHub Actions (recomendado)

1. Ir a **Actions → Generar Reporte Mensual → Run workflow**
2. Completar `year` y `month`
3. El reporte queda en `https://<org>.github.io/<repo>/reports/YYYY-MM/`

### Localmente

```bash
# Instalar dependencias
pip install -r scripts/requirements.txt

# Con Application Default Credentials (gcloud auth application-default login)
python scripts/run_report.py --year 2026 --month 3

# Con Service Account JSON
export GCP_SA_KEY=$(cat mi-service-account.json)
python scripts/run_report.py --year 2026 --month 3

# Dry run (sin ejecutar queries, para probar el template)
python scripts/run_report.py --year 2026 --month 3 --dry-run

# Actualizar index.html
python scripts/update_index.py
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

### Secrets (Settings → Secrets and variables → Actions)

| Secret | Descripción |
|--------|-------------|
| `GCP_SA_KEY` | JSON completo del Service Account de BigQuery |

### Variables (Settings → Secrets and variables → Actions → Variables)

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | `meli-bi-data` | GCP Project ID |

### GitHub Pages (Settings → Pages)

- **Source**: GitHub Actions
- El workflow lo configura automáticamente en cada ejecución

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
