"""
CES - Facilidad de uso por seccion

Lee Q1 de cada survey desde Google Sheets y clasifica en Facil / Neutro / Dificil.
Escala en portugues: "Muito dificil" / "Dificil" / "Nem dificil nem facil" / "Facil" / "Muito facil"
"""
import sys
from pathlib import Path

import pandas as pd

TITLE = "CES - Facilidad de uso por seccion"
SECTION = "product"
DESCRIPTION = "Que tan facil/dificil encuentran la herramienta los usuarios que respondieron en el mes"
ORDER = 1

SURVEY_ORDER = ["simulador_costos_lite", "simulador_costos", "costos", "pricing"]
SHORT_NAMES = {
    "simulador_costos_lite": "Simulador Costos LITE",
    "simulador_costos": "Simulador Costos",
    "costos": "Costos",
    "pricing": "Pricing",
}

DRY_RUN_DATA = pd.DataFrame({
    "Seccion":      ["Simulador Costos LITE", "Simulador Costos", "Costos", "Pricing"],
    "Facil %":      [65.2, 71.8, 58.3, 69.4],
    "Neutro %":     [20.1, 18.5, 22.7, 19.2],
    "Dificil %":    [14.7,  9.7, 19.0, 11.4],
    "Respuestas":   [234,   189,  156,   312],
})


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.sheets_reader import SheetsReader, classify_ces

    reader = SheetsReader()
    surveys_cfg = config.get("qualtrics", {}).get("surveys", {})

    rows = []
    for key in SURVEY_ORDER:
        sv = surveys_cfg.get(key, {})
        tab = sv.get("sheets_tab")
        ces_col = sv.get("ces_column", "Q1")
        short = SHORT_NAMES[key]

        if not tab:
            rows.append({"Seccion": short, "Facil %": None, "Neutro %": None,
                         "Dificil %": None, "Respuestas": 0, "Nota": "sheets_tab no configurado"})
            continue

        try:
            df = reader.get_survey_data(tab, params["start_date"], params["end_date"])

            if df.empty or ces_col not in df.columns:
                rows.append({"Seccion": short, "Facil %": None, "Neutro %": None,
                             "Dificil %": None, "Respuestas": 0, "Nota": "Sin respuestas en el periodo"})
                continue

            labels = df[ces_col].dropna().astype(str).str.strip()
            labels = labels[labels.str.len() > 1]
            total = len(labels)

            if total == 0:
                rows.append({"Seccion": short, "Facil %": None, "Neutro %": None,
                             "Dificil %": None, "Respuestas": 0, "Nota": "Sin respuestas validas"})
                continue

            cats = labels.apply(classify_ces)
            rows.append({
                "Seccion":    short,
                "Facil %":    round(100 * (cats == "Facil").sum()   / total, 1),
                "Neutro %":   round(100 * (cats == "Neutro").sum()  / total, 1),
                "Dificil %":  round(100 * (cats == "Dificil").sum() / total, 1),
                "Respuestas": total,
            })
        except Exception as e:
            rows.append({"Seccion": short, "Facil %": None, "Neutro %": None,
                         "Dificil %": None, "Respuestas": 0, "Nota": f"Error: {e}"})

    return pd.DataFrame(rows)
