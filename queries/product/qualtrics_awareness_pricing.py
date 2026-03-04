"""
Awareness de Pricing antes de ingresar a la seccion

Lee Q2 del survey de Pricing desde Google Sheets.
Pregunta: "Voce sabia que tinha disponivel para voce as taxas especiais do Mercado Pago?"
"""
import sys
from pathlib import Path

import pandas as pd

TITLE = "Awareness - Conocimiento previo de Pricing"
SECTION = "product"
DESCRIPTION = "Porcentaje de usuarios que conocian la seccion de Pricing antes de ingresar"
ORDER = 4
CHART_TYPE = "doughnut"

DRY_RUN_DATA = pd.DataFrame({
    "Respuesta":   ["Sim, sabia", "Nao sabia", "Ja vi mas nao usei"],
    "Respuestas":  [142, 109, 61],
    "% del total": [45.5, 34.9, 19.6],
})


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.sheets_reader import SheetsReader

    surveys_cfg = config.get("qualtrics", {}).get("surveys", {})
    pricing_cfg = surveys_cfg.get("pricing", {})
    tab = pricing_cfg.get("sheets_tab")
    awareness_col = pricing_cfg.get("awareness_column", "Q2")

    if not tab:
        return pd.DataFrame({"Aviso": ["sheets_tab de pricing no configurado en config/surveys.yaml"]})

    reader = SheetsReader()
    try:
        df = reader.get_survey_data(tab, params["start_date"], params["end_date"])

        if df.empty or awareness_col not in df.columns:
            return pd.DataFrame({"Aviso": ["Sin respuestas en el periodo"]})

        counts = (
            df[awareness_col]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s.str.len() > 1]
            .value_counts()
            .reset_index()
        )
        counts.columns = ["Respuesta", "Respuestas"]
        total = counts["Respuestas"].sum()
        counts["% del total"] = (counts["Respuestas"] / total * 100).round(1)
        return counts

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})
