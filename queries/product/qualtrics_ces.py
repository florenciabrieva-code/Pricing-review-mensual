"""
CES - Tendencia mensual de facilidad de uso (ultimos 12 meses)

Agrega Q1 de todos los surveys desde Google Sheets, clasifica en
Facil / Neutro / Dificil y agrupa por mes.
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

TITLE = "CES - Tendencia mensual"
SECTION = "product"
DESCRIPTION = "Evolucion mensual del CES agregado de todas las secciones (ultimos 12 meses)"
ORDER = 1
CHART_TYPE = "bar_grouped"

SURVEY_ORDER = ["simulador_costos_lite", "simulador_costos", "costos", "pricing"]

MONTH_NAMES = {
    "01": "ene", "02": "feb", "03": "mar", "04": "abr",
    "05": "may", "06": "jun", "07": "jul", "08": "ago",
    "09": "sep", "10": "oct", "11": "nov", "12": "dic",
}

DRY_RUN_DATA = pd.DataFrame({
    "Mes":        ["ene", "feb", "mar", "abr", "may", "jun",
                   "jul", "ago", "sep", "oct", "nov", "dic"],
    "Facil %":    [55, 52, 55, 53, 54, 55, 53, 57, 55, 53, 55, 55],
    "Neutro %":   [25, 25, 24, 26, 24, 24, 24, 23, 23, 25, 24, 24],
    "Dificil %":  [20, 23, 21, 21, 22, 21, 23, 20, 22, 22, 21, 21],
    "Respuestas": [312, 298, 334, 289, 301, 315, 278, 342, 295, 308, 321, 287],
})


def _trend_start(end_date_str: str) -> str:
    """Devuelve el primer dia de hace 11 meses (ventana de 12 meses)."""
    end = date.fromisoformat(end_date_str)
    m = end.month - 11
    y = end.year
    if m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1).isoformat()


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.sheets_reader import SheetsReader, classify_ces

    reader = SheetsReader()
    surveys_cfg = config.get("qualtrics", {}).get("surveys", {})
    start_trend = _trend_start(params["end_date"])

    all_rows = []
    for key in SURVEY_ORDER:
        sv = surveys_cfg.get(key, {})
        tab = sv.get("sheets_tab")
        ces_col = sv.get("ces_column", "Q1")
        if not tab:
            continue
        try:
            df = reader.get_survey_data(tab, start_trend, params["end_date"])
            if df.empty or ces_col not in df.columns or "StartDate" not in df.columns:
                continue
            sub = df[["StartDate", ces_col]].copy()
            sub["_dt"] = pd.to_datetime(sub["StartDate"], errors="coerce")
            sub = sub.dropna(subset=["_dt"])
            sub["_mes"] = sub["_dt"].dt.strftime("%Y-%m")
            sub["_cat"] = sub[ces_col].astype(str).str.strip().apply(classify_ces)
            all_rows.append(sub[["_mes", "_cat"]])
        except Exception:
            continue

    if not all_rows:
        return pd.DataFrame({"Aviso": ["Sin respuestas en el periodo"]})

    combined = pd.concat(all_rows, ignore_index=True)
    combined = combined[combined["_cat"].isin(["Facil", "Neutro", "Dificil"])]

    grouped = combined.groupby(["_mes", "_cat"]).size().reset_index(name="cnt")
    totals  = combined.groupby("_mes").size().reset_index(name="total")
    merged  = grouped.merge(totals, on="_mes")
    merged["pct"] = (merged["cnt"] / merged["total"] * 100).round(1)

    pivot = (
        merged.pivot(index="_mes", columns="_cat", values="pct")
        .reindex(columns=["Facil", "Neutro", "Dificil"])
        .reset_index()
        .rename(columns={"Facil": "Facil %", "Neutro": "Neutro %", "Dificil": "Dificil %"})
    )
    pivot = pivot.merge(totals.rename(columns={"total": "Respuestas"}), on="_mes")
    pivot["Mes"] = pivot["_mes"].apply(
        lambda x: MONTH_NAMES.get(x[-2:], x) if isinstance(x, str) else x
    )
    return pivot[["Mes", "Facil %", "Neutro %", "Dificil %", "Respuestas"]]
