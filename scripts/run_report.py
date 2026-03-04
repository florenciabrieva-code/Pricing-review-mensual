#!/usr/bin/env python3
"""
Monthly Review Report Generator
Conecta a BigQuery y Qualtrics, corre todas las queries del mes y genera un HTML.

Uso:
    python scripts/run_report.py --year 2026 --month 3
"""

import argparse
import calendar
import importlib.util
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
    """Carga .sql (BigQuery) y .py (fuentes Python como Qualtrics)."""
    queries = []

    # --- SQL queries ---
    for sql_file in sorted(queries_dir.rglob("*.sql")):
        content = sql_file.read_text(encoding="utf-8")
        meta = parse_sql_metadata(content)
        folder_section = sql_file.parent.name
        section = meta.get("section", folder_section)
        queries.append(
            {
                "type": "sql",
                "file": str(sql_file.relative_to(ROOT)),
                "section": section,
                "title": meta.get("title", sql_file.stem.replace("_", " ").title()),
                "description": meta.get("description", ""),
                "sql": content,
                "order": int(meta.get("order", 99)),
            }
        )

    # --- Python data sources (Qualtrics, APIs, etc.) ---
    for py_file in sorted(queries_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, str(py_file))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"WARNING: No se pudo cargar {py_file.name}: {e}")
            continue

        if not hasattr(mod, "run"):
            continue

        folder_section = py_file.parent.name
        queries.append(
            {
                "type": "python",
                "file": str(py_file.relative_to(ROOT)),
                "section": getattr(mod, "SECTION", folder_section),
                "title": getattr(mod, "TITLE", py_file.stem.replace("_", " ").title()),
                "description": getattr(mod, "DESCRIPTION", ""),
                "order": int(getattr(mod, "ORDER", 99)),
                "chart_type": getattr(mod, "CHART_TYPE", None),
                "run_fn": mod.run,
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


def load_config() -> dict:
    """Carga configuracion desde variables de entorno y config/surveys.yaml."""
    config = {
        "QUALTRICS_API_TOKEN": os.getenv("QUALTRICS_API_TOKEN", ""),
        "QUALTRICS_DATACENTER": os.getenv("QUALTRICS_DATACENTER", ""),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID", "meli-bi-data"),
    }
    surveys_yaml = ROOT / "config" / "surveys.yaml"
    if surveys_yaml.exists():
        try:
            import yaml
            with open(surveys_yaml, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}
            config.update(yaml_config)
        except Exception as e:
            print(f"WARNING: No se pudo cargar config/surveys.yaml: {e}")
    return config


def substitute_params(sql: str, params: dict) -> str:
    for key, value in params.items():
        sql = sql.replace(f"{{{{ {key} }}}}", value)
    return sql


def _df_to_json(df: pd.DataFrame, chart_type: str | None) -> str | None:
    """Serializa un DataFrame a JSON (lista de objetos) para uso en Chart.js."""
    if chart_type is None or df is None or df.empty:
        return None
    try:
        clean = df.where(df.notna(), other=None)
        return clean.to_json(orient="records", force_ascii=False)
    except Exception:
        return None


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


def build_bq_client(project: str) -> bigquery.Client:
    sa_key = os.getenv("GCP_SA_KEY")
    if sa_key:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa_key),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=project, credentials=creds)
    return bigquery.Client(project=project)


def run_all_queries(bq_client, queries, params, config, dry_run=False):
    """Ejecuta todas las queries (SQL y Python) y devuelve resultados por seccion."""
    sections: dict[str, list] = {}

    for q in queries:
        section = q["section"]
        if section not in sections:
            sections[section] = []

        print(f"  > [{section}] {q['title']} ...", end=" ", flush=True)

        chart_type = q.get("chart_type")
        df_json = None

        if q["type"] == "python":
            try:
                result = q["run_fn"](params, config, dry_run=dry_run)
                status = "dry_run" if dry_run else "ok"
                error = None
                # Multi-output: run() devuelve lista de {title, description, df}
                if isinstance(result, list):
                    print(f"{'dry-run' if dry_run else 'OK'} ({len(result)} bloques)")
                    for sub in result:
                        sub_df = sub.get("df", pd.DataFrame())
                        sections[section].append({
                            "title":       sub.get("title", q["title"]),
                            "description": sub.get("description", q["description"]),
                            "file":        q["file"],
                            "table_html":  df_to_html(sub_df),
                            "chart_type":  chart_type,
                            "df_json":     _df_to_json(sub_df, chart_type),
                            "status":      status,
                            "error":       None,
                        })
                    continue  # ya se agregaron los sub-items
                else:
                    df = result
                    table_html = df_to_html(df)
                    df_json = _df_to_json(df, chart_type)
                    print(f"{'dry-run' if dry_run else 'OK'} ({len(df)} filas)")
            except Exception as e:
                table_html = f'<p class="error">Error: {e}</p>'
                df_json = None
                status = "error"
                error = str(e)
                print(f"ERROR: {e}")

        else:  # SQL
            sql = substitute_params(q["sql"], params)
            if dry_run:
                table_html = '<p class="dry-run">Modo dry-run: query SQL no ejecutada.</p>'
                df_json = None
                status = "dry_run"
                error = None
                print("dry-run")
            else:
                try:
                    df = bq_client.query(sql).to_dataframe()
                    table_html = df_to_html(df)
                    df_json = _df_to_json(df, chart_type)
                    status = "ok"
                    error = None
                    print(f"OK ({len(df)} filas)")
                except Exception as e:
                    table_html = f'<p class="error">Error: {e}</p>'
                    df_json = None
                    status = "error"
                    error = str(e)
                    print(f"ERROR: {e}")

        sections[section].append(
            {
                "title": q["title"],
                "description": q["description"],
                "file": q["file"],
                "table_html": table_html,
                "chart_type": chart_type,
                "df_json": df_json,
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
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument(
        "--project",
        default=os.getenv("GCP_PROJECT_ID", "meli-bi-data"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No ejecuta queries reales (util para probar el template)",
    )
    args = parser.parse_args()

    if not 1 <= args.month <= 12:
        print("ERROR: --month debe estar entre 1 y 12")
        sys.exit(1)

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

    config = load_config()
    queries = load_queries(ROOT / "queries")

    sql_count = sum(1 for q in queries if q["type"] == "sql")
    py_count = sum(1 for q in queries if q["type"] == "python")
    print(f"Queries encontradas: {len(queries)} ({sql_count} SQL, {py_count} Python)\n")

    if not queries:
        print("ERROR: No se encontraron queries en queries/")
        sys.exit(1)

    bq_client = None
    if sql_count > 0 and not args.dry_run:
        bq_client = build_bq_client(args.project)

    sections = run_all_queries(bq_client, queries, params, config, dry_run=args.dry_run)
    render_report(sections, params, output_path)


if __name__ == "__main__":
    main()
