"""
Tiempo de respuesta promedio por survey

Lee el campo "Duration (in seconds)" desde Google Sheets.
"""
import sys
from pathlib import Path

import pandas as pd

TITLE = "Tiempo de respuesta - Encuestas UX"
SECTION = "product"
DESCRIPTION = "Tiempo promedio y mediana para completar cada encuesta en el mes"
ORDER = 2

SURVEY_ORDER = ["simulador_costos_lite", "simulador_costos", "costos", "pricing"]
SHORT_NAMES = {
    "simulador_costos_lite": "Simulador Costos LITE",
    "simulador_costos":      "Simulador Costos",
    "costos":                "Costos",
    "pricing":               "Pricing",
}

DRY_RUN_DATA = pd.DataFrame({
    "Seccion":          ["Simulador Costos LITE", "Simulador Costos", "Costos", "Pricing"],
    "Promedio (min)":   [3.2, 4.1, 3.8, 5.2],
    "Mediana (min)":    [2.8, 3.5, 3.2, 4.7],
    "Min (min)":        [0.5, 0.8, 0.6, 1.0],
    "Max (min)":        [18.3, 22.1, 19.7, 28.4],
    "Respuestas":       [234, 189, 156, 312],
})

DURATION_COL = "Duration (in seconds)"


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.sheets_reader import SheetsReader

    reader = SheetsReader()
    surveys_cfg = config.get("qualtrics", {}).get("surveys", {})

    rows = []
    for key in SURVEY_ORDER:
        sv = surveys_cfg.get(key, {})
        tab = sv.get("sheets_tab")
        short = SHORT_NAMES[key]

        if not tab:
            rows.append({"Seccion": short, "Promedio (min)": None, "Mediana (min)": None,
                         "Min (min)": None, "Max (min)": None, "Respuestas": 0})
            continue

        try:
            df = reader.get_survey_data(tab, params["start_date"], params["end_date"])

            dur_col = next((c for c in df.columns if "duration" in c.lower()), None)
            if df.empty or not dur_col:
                rows.append({"Seccion": short, "Promedio (min)": None, "Mediana (min)": None,
                             "Min (min)": None, "Max (min)": None, "Respuestas": 0,
                             "Nota": "Sin datos de duracion"})
                continue

            secs = pd.to_numeric(df[dur_col], errors="coerce").dropna()
            # Filtrar outliers: < 20 seg (bot) o > 60 min
            secs = secs[(secs >= 20) & (secs <= 3600)]
            mins = secs / 60

            rows.append({
                "Seccion":         short,
                "Promedio (min)":  round(mins.mean(), 1),
                "Mediana (min)":   round(mins.median(), 1),
                "Min (min)":       round(mins.min(), 1),
                "Max (min)":       round(mins.max(), 1),
                "Respuestas":      len(mins),
            })
        except Exception as e:
            rows.append({"Seccion": short, "Promedio (min)": None, "Mediana (min)": None,
                         "Min (min)": None, "Max (min)": None, "Respuestas": 0, "Nota": f"Error: {e}"})

    return pd.DataFrame(rows)
