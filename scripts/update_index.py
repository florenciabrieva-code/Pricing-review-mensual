#!/usr/bin/env python3
"""
Regenera el index.html raíz con links a todos los reportes disponibles.
Se ejecuta automáticamente después de cada generación de reporte.
"""

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPORTS_DIR = ROOT / "reports"
OUTPUT = ROOT / "index.html"

MONTH_NAMES_ES = {
    "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
    "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
    "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre",
}


def get_available_reports() -> list[dict]:
    reports = []
    for folder in sorted(REPORTS_DIR.iterdir(), reverse=True):
        if not folder.is_dir():
            continue
        if not re.match(r"^\d{4}-\d{2}$", folder.name):
            continue
        index_file = folder / "index.html"
        if not index_file.exists():
            continue
        year, month = folder.name.split("-")
        reports.append(
            {
                "folder": folder.name,
                "year": year,
                "month": month,
                "month_name": MONTH_NAMES_ES.get(month, month),
                "label": f"{MONTH_NAMES_ES.get(month, month)} {year}",
                "url": f"reports/{folder.name}/index.html",
                "modified": index_file.stat().st_mtime,
            }
        )
    return reports


def render_index(reports: list[dict]) -> str:
    cards_html = ""
    for r in reports:
        cards_html += f"""
        <a href="{r['url']}" class="report-card">
            <div class="card-month">{r['month_name']}</div>
            <div class="card-year">{r['year']}</div>
            <div class="card-arrow">→</div>
        </a>"""

    if not cards_html:
        cards_html = '<p class="empty">Todavía no hay reportes generados.</p>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Monthly Review</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #1a1a1a; }}
    header {{ background: #009ee3; color: white; padding: 40px 48px; }}
    header h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }}
    header p {{ margin-top: 6px; opacity: 0.85; font-size: 1rem; }}
    main {{ max-width: 960px; margin: 48px auto; padding: 0 24px; }}
    h2 {{ font-size: 1.1rem; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }}
    .report-card {{
      display: flex; flex-direction: column; justify-content: space-between;
      background: white; border-radius: 12px; padding: 24px 20px;
      text-decoration: none; color: inherit;
      border: 1px solid #e5e5e5;
      transition: box-shadow 0.15s, transform 0.15s;
    }}
    .report-card:hover {{ box-shadow: 0 4px 20px rgba(0,0,0,0.1); transform: translateY(-2px); }}
    .card-month {{ font-size: 1.2rem; font-weight: 700; color: #009ee3; }}
    .card-year {{ font-size: 0.95rem; color: #888; margin-top: 4px; }}
    .card-arrow {{ font-size: 1.1rem; color: #ccc; margin-top: 16px; text-align: right; }}
    .empty {{ color: #888; font-size: 1rem; padding: 40px 0; }}
    footer {{ text-align: center; padding: 40px; color: #aaa; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <header>
    <h1>Monthly Review</h1>
    <p>Reportes mensuales de Negocio · Producto · CX</p>
  </header>
  <main>
    <h2>Reportes disponibles</h2>
    <div class="grid">{cards_html}
    </div>
  </main>
  <footer>Actualizado el {date.today().isoformat()}</footer>
</body>
</html>"""


def main():
    reports = get_available_reports()
    html = render_index(reports)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"index.html actualizado — {len(reports)} reporte(s) listado(s)")
    for r in reports:
        print(f"  • {r['label']}")


if __name__ == "__main__":
    main()
