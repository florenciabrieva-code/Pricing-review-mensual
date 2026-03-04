"""
CES - Tendencia mensual por encuesta (ultimos 12 meses)

Devuelve una card por survey con la evolucion mensual de Facil/Neutro/Dificil.
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

TITLE = "CES - Tendencia mensual"
SECTION = "product"
DESCRIPTION = "Evolucion mensual del CES por seccion (ultimos 12 meses)"
ORDER = 1
CHART_TYPE = "bar_grouped"

SURVEY_ORDER = ["simulador_costos_lite", "simulador_costos", "costos", "pricing"]
SHORT_NAMES = {
    "simulador_costos_lite": "Simulador Costos LITE",
    "simulador_costos":      "Simulador Costos",
    "costos":                "Costos",
    "pricing":               "Pricing",
}
MONTH_NAMES = {
    "01": "ene", "02": "feb", "03": "mar", "04": "abr",
    "05": "may", "06": "jun", "07": "jul", "08": "ago",
    "09": "sep", "10": "oct", "11": "nov", "12": "dic",
}

# DRY_RUN: una lista de dataframes, uno por encuesta
_BASE = [55, 52, 55, 53, 54, 55, 53, 57, 55, 53, 55, 55]
_MESES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
_DRY_SURVEYS = {
    "simulador_costos_lite": {"f": [65,62,65,63,64,65,63,67,65,63,65,65],
                               "n": [20,20,19,21,19,19,19,18,18,20,19,19],
                               "d": [15,18,16,16,17,16,18,15,17,17,16,16],
                               "r": [80,75,85,70,78,82,68,90,76,82,84,73]},
    "simulador_costos":       {"f": [70,68,72,69,71,70,68,73,71,69,70,72],
                               "n": [19,20,18,21,19,19,20,17,18,20,19,18],
                               "d": [11,12,10,10,10,11,12, 10,11,11,11,10],
                               "r": [65,60,72,58,65,69,55,78,63,68,70,61]},
    "costos":                 {"f": [58,55,58,56,57,58,56,60,58,56,58,58],
                               "n": [23,24,23,25,23,23,23,22,22,24,23,23],
                               "d": [19,21,19,19,20,19,21,18,20,20,19,19],
                               "r": [55,50,60,48,52,57,46,65,52,55,58,50]},
    "pricing":                {"f": [69,66,69,67,68,69,67,71,69,67,69,69],
                               "n": [19,20,19,21,19,19,20,18,18,20,19,19],
                               "d": [12,14,12,12,13,12,13,11,13,13,12,12],
                               "r": [112,105,118,100,108,115,96,124,108,112,119,105]},
}


def _make_dry_run_df(key):
    v = _DRY_SURVEYS[key]
    return pd.DataFrame({
        "Mes":        _MESES,
        "Facil %":    v["f"],
        "Neutro %":   v["n"],
        "Dificil %":  v["d"],
        "Respuestas": v["r"],
    })


def _trend_start(end_date_str: str) -> str:
    end = date.fromisoformat(end_date_str)
    m = end.month - 11
    y = end.year
    if m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1).isoformat()


def _build_monthly_df(df_raw: pd.DataFrame, ces_col: str) -> pd.DataFrame:
    """Clasifica CES y agrega por mes."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.sheets_reader import classify_ces

    sub = df_raw[["StartDate", ces_col]].copy()
    sub["_dt"] = pd.to_datetime(sub["StartDate"], errors="coerce")
    sub = sub.dropna(subset=["_dt"])
    sub["_mes"] = sub["_dt"].dt.strftime("%Y-%m")
    sub["_cat"] = sub[ces_col].astype(str).str.strip().apply(classify_ces)
    sub = sub[sub["_cat"].isin(["Facil", "Neutro", "Dificil"])]

    if sub.empty:
        return pd.DataFrame()

    grouped = sub.groupby(["_mes", "_cat"]).size().reset_index(name="cnt")
    totals  = sub.groupby("_mes").size().reset_index(name="total")
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


def run(params: dict, config: dict, dry_run: bool = False) -> list:
    """Devuelve lista de {title, description, df} — una card por encuesta."""
    if dry_run:
        return [
            {
                "title": f"CES - {SHORT_NAMES[k]}",
                "description": f"Tendencia mensual de facilidad de uso - {SHORT_NAMES[k]}",
                "df": _make_dry_run_df(k),
            }
            for k in SURVEY_ORDER
        ]

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.sheets_reader import SheetsReader

    reader = SheetsReader()
    surveys_cfg = config.get("qualtrics", {}).get("surveys", {})
    start_trend = _trend_start(params["end_date"])

    results = []
    for key in SURVEY_ORDER:
        sv = surveys_cfg.get(key, {})
        tab = sv.get("sheets_tab")
        ces_col = sv.get("ces_column", "Q1")
        short = SHORT_NAMES[key]

        if not tab:
            results.append({
                "title": f"CES - {short}",
                "description": f"sheets_tab no configurado para {short}",
                "df": pd.DataFrame({"Aviso": ["sheets_tab no configurado"]}),
            })
            continue

        try:
            df_raw = reader.get_survey_data(tab, start_trend, params["end_date"])
            if df_raw.empty or ces_col not in df_raw.columns:
                df_out = pd.DataFrame({"Aviso": ["Sin respuestas en el periodo"]})
            else:
                df_out = _build_monthly_df(df_raw, ces_col)
                if df_out.empty:
                    df_out = pd.DataFrame({"Aviso": ["Sin respuestas validas"]})
        except Exception as e:
            df_out = pd.DataFrame({"Error": [str(e)]})

        results.append({
            "title":       f"CES - {short}",
            "description": f"Tendencia mensual de facilidad de uso - {short}",
            "df":          df_out,
        })

    return results
