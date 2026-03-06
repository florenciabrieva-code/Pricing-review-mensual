"""
CES - Tendencia mensual por encuesta (ultimos 6 meses)

Devuelve 4 cards (half-width, 2x2 grid):
  Fila 1: Simulador Costos LITE | Simulador Costos
  Fila 2: Pricing               | Costos
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

TITLE = "CES - Tendencia mensual"
SECTION = "product"
DESCRIPTION = "Evolucion mensual del CES por seccion (ultimos 6 meses)"
ORDER = 1
CHART_TYPE = "line"

# Orden de display: SimLite, Sim, Pricing, Costos
SURVEY_ORDER = ["simulador_costos_lite", "simulador_costos", "pricing", "costos"]
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

_MESES_6 = ["oct", "nov", "dic", "ene", "feb", "mar"]
_DRY = {
    "simulador_costos_lite": {"f": [63,65,65,65,62,65], "n": [20,19,19,20,20,19], "d": [17,16,16,15,18,16], "r": [82,84,73,80,75,85]},
    "simulador_costos":      {"f": [69,70,72,70,68,72], "n": [20,19,18,19,20,18], "d": [11,11,10,11,12,10], "r": [68,70,61,65,60,72]},
    "pricing":               {"f": [67,69,69,69,66,69], "n": [20,19,19,19,20,19], "d": [13,12,12,12,14,12], "r": [112,119,105,112,105,118]},
    "costos":                {"f": [56,58,58,58,55,58], "n": [24,23,23,23,24,23], "d": [20,19,19,19,21,19], "r": [55,58,50,55,50,60]},
}


def _make_dry_df(key):
    v = _DRY[key]
    return pd.DataFrame({
        "Mes":        _MESES_6,
        "Facil %":    v["f"],
        "Neutro %":   v["n"],
        "Dificil %":  v["d"],
        "Respuestas": v["r"],
    })


def _trend_start(end_date_str: str) -> str:
    """Primer dia de hace 5 meses (ventana de 6 meses)."""
    end = date.fromisoformat(end_date_str)
    m = end.month - 5
    y = end.year
    if m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1).isoformat()


def _build_monthly_df(df_raw: pd.DataFrame, ces_col: str) -> pd.DataFrame:
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
    """Devuelve 4 cards half-width — Fila 1: SimLite+Sim, Fila 2: Pricing+Costos."""
    if dry_run:
        return [
            {
                "title":       SHORT_NAMES[k],
                "description": "",
                "df":          _make_dry_df(k),
                "half":        True,
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
        sv      = surveys_cfg.get(key, {})
        tab     = sv.get("sheets_tab")
        ces_col = sv.get("ces_column", "Q1")
        short   = SHORT_NAMES[key]

        if not tab:
            df_out = pd.DataFrame({"Aviso": ["sheets_tab no configurado"]})
        else:
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
            "title":       short,
            "description": "",
            "df":          df_out,
            "half":        True,
        })

    return results
