#!/usr/bin/env python3
"""
Monthly Review Report Generator
Conecta a BigQuery, corre todas las queries del mes y genera un HTML.

Uso:
    python scripts/run_report.py --year 2026 --month 3
"""

import argparse
import calendar
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import jinja2
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

ROOT = Path(__file__).parent.parent

SECTION_ORDER = {"business": 0, "product": 1, "cx": 2}
SECTION_LABELS = {
    "business": "Negocio",
    "product": "Producto",
    "cx": "CX",
}


def get_month_range(year: int, month: int) -> tuple[str, str]:
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return first.isoformat(), last.isoformat()


def parse_sql_metadata(content: str) -> dict:
    """Lee los metadatos del bloque de comentarios al inicio del archivo."""
    meta = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("--"):
            break
        m = re.match(r"^--\s*(\w+):\s*(.+)$", stripped)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta


def load_queries(queries_dir: Path) -> list[dict]:
    queries = []
    for sql_file in sorted(queries_dir.rglob("*.sql")):
        content = sql_file.read_text(encoding="utf-8")
        meta = parse_sql_metadata(content)
        folder_section = sql_file.parent.name
        section = meta.get("section", folder_section)
        queries.append(
            {
                "file": str(sql_file.relative_to(ROOT)),
                "section": section,
                "title": meta.get("title", sql_file.stem.replace("_", " ").title()),
                "description": meta.get("description", ""),
                "sql": content,
                "order": int(meta.get("order", 99)),
            }
        )
    queries.sort(
        key=lambda x: (
            SECTION_ORDER.get(x["section"], 99),
            x["order"],
            x["title"],
        )
    )
    return queries


def substitute_params(sql: str, params: dict) -> str:
    for key, value in params.items():
        sql = sql.replace(f"{{{{ {key} }}}}", value)
    return sql


def df_to_html(df: pd.DataFrame) -> str:
    if df.empty:
        return '<p class="no-data">Sin datos para el periodo seleccionado.</p>'
    return df.to_html(
        index=False,
        classes="data-table",
        border=0,
        na_rep="-",
        float_format=lambda x: f"{x:,.2f}",
    )


def build_client(project: str) -> bigquery.Client:
    sa_key = os.getenv("GCP_SA_KEY")
    if sa_key:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa_key),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=project, credentials=creds)
    # Usa Application Default Credentials (gcloud auth)
    return bigquery.Client(project=project)


def run_all_queries(client, queries, params, dry_run=False):
    """Ejecuta todas las queries y devuelve resultados por sección."""
    sections: dict[str, list] = {}

    for q in queries:
        section = q["section"]
        if section not in sections:
            sections[section] = []

        sql = substitute_params(q["sql"], params)

        print(f"  > [{section}] {q['title']} ...", end=" ", flush=True)

        if dry_run:
            table_html = '<p class="dry-run">Modo dry-run: query no ejecutada.</p>'
            status = "dry_run"
            error = None
        else:
            try:
                df = client.query(sql).to_dataframe()
                table_html = df_to_html(df)
                status = "ok"
                error = None
                print(f"OK ({len(df)} filas)")
            except Exception as e:
                table_html = f'<p class="error">Error: {e}</p>'
                status = "error"
                error = str(e)
                print(f"ERROR: {e}")

        sections[section].append(
            {
                "title": q["title"],
                "description": q["description"],
                "file": q["file"],
                "table_html": table_html,
                "status": status,
                "error": error,
            }
        )

    return sections


def render_report(sections, params, output_path: Path):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROOT / "templates")),
        autoescape=False,
    )
    template = env.get_template("report.html.j2")

    month_names_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }

    html = template.render(
        sections=sections,
        section_labels=SECTION_LABELS,
        params=params,
        month_name=month_names_es[int(params["month"])],
        generated_at=date.today().isoformat(),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"\nReporte generado: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Genera el reporte mensual HTML")
    parser.add_argument("--year", type=int, required=True, help="Año (ej: 2026)")
    parser.add_argument("--month", type=int, required=True, help="Mes 1-12 (ej: 3)")
    parser.add_argument(
        "--project",
        default=os.getenv("GCP_PROJECT_ID", "meli-bi-data"),
        help="GCP project ID",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No ejecuta queries, genera HTML vacío (para pruebas de template)",
    )
    args = parser.parse_args()

    if not 1 <= args.month <= 12:
        print("ERROR: --month debe estar entre 1 y 12")
        sys.exit(1)

    # Calcular fechas
    start_date, end_date = get_month_range(args.year, args.month)
    prev_month_date = date(args.year, args.month, 1) - timedelta(days=1)
    prev_start, prev_end = get_month_range(prev_month_date.year, prev_month_date.month)

    params = {
        "year": str(args.year),
        "month": f"{args.month:02d}",
        "start_date": start_date,
        "end_date": end_date,
        "prev_start_date": prev_start,
        "prev_end_date": prev_end,
        "project": args.project,
    }

    output_path = ROOT / "reports" / f"{args.year}-{args.month:02d}" / "index.html"

    print(f"\n{'='*50}")
    print(f"Monthly Review - {args.year}-{args.month:02d}")
    print(f"Periodo: {start_date} -> {end_date}")
    print(f"Proyecto BQ: {args.project}")
    print(f"Output: {output_path}")
    print(f"{'='*50}\n")

    queries = load_queries(ROOT / "queries")
    print(f"Queries encontradas: {len(queries)}\n")

    if not queries:
        print("ERROR: No se encontraron archivos .sql en queries/")
        sys.exit(1)

    client = None if args.dry_run else build_client(args.project)
    sections = run_all_queries(client, queries, params, dry_run=args.dry_run)
    render_report(sections, params, output_path)


if __name__ == "__main__":
    main()
