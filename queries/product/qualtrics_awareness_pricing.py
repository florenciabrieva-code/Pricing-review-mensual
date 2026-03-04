"""
Awareness de Pricing antes de ingresar a la seccion (Qualtrics)

Solo aplica al survey [MLB] VOC Pricing.
Pregunta especifica que mide si el usuario conocia la seccion antes de ingresar.
"""
import os
import sys
from pathlib import Path

import pandas as pd

TITLE = "Awareness - Conocimiento previo de Pricing"
SECTION = "product"
DESCRIPTION = "Porcentaje de usuarios que conocian la seccion de Pricing antes de ingresar"
ORDER = 4

DRY_RUN_DATA = pd.DataFrame(
    {
        "Respuesta": ["Si, la conocia", "No, es la primera vez", "La vi pero nunca la use"],
        "Respuestas": [142, 109, 61],
        "% del total": [45.5, 34.9, 19.6],
    }
)


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    api_token = config.get("QUALTRICS_API_TOKEN") or os.getenv("QUALTRICS_API_TOKEN")
    datacenter = config.get("QUALTRICS_DATACENTER") or os.getenv("QUALTRICS_DATACENTER")

    if not api_token or not datacenter:
        return pd.DataFrame({"Aviso": ["Configurar QUALTRICS_API_TOKEN y QUALTRICS_DATACENTER en .env"]})

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.qualtrics_client import QualtricsClient

    surveys_config = config.get("qualtrics", {}).get("surveys", {})
    pricing_cfg = surveys_config.get("pricing", {})
    survey_id = pricing_cfg.get("id")
    awareness_qid = pricing_cfg.get("awareness_question_id")

    if not survey_id or not awareness_qid:
        return pd.DataFrame(
            {"Aviso": ["Configurar pricing.awareness_question_id en config/surveys.yaml"]}
        )

    client = QualtricsClient(api_token, datacenter)

    try:
        df = client.export_responses(
            survey_id,
            params["start_date"],
            params["end_date"],
            use_labels=True,  # Traer texto de las opciones
        )

        if awareness_qid not in df.columns or df.empty:
            return pd.DataFrame({"Aviso": ["Sin respuestas en el periodo"]})

        counts = (
            df[awareness_qid]
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
