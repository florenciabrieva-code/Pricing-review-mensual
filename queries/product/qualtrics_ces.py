"""
CES - Facilidad de uso por seccion (Qualtrics)

Q1: "Que tan dificil o facil fue utilizar esta herramienta?"
Muestra distribucion Facil / Neutro / Dificil para cada survey del mes.
"""
import os
import sys
from pathlib import Path

import pandas as pd

TITLE = "CES - Facilidad de uso por seccion"
SECTION = "product"
DESCRIPTION = "Distribucion de facilidad/dificultad percibida por los usuarios que respondieron en el mes"
ORDER = 1

SURVEY_NAMES = [
    "[MLB] VOC Simulador de Costos LITE",
    "[MLB] VOC Simulador de Costos",
    "[MLB] VOC Costos",
    "[MLB] VOC Pricing",
]

SHORT_NAMES = {
    "[MLB] VOC Simulador de Costos LITE": "Simulador Costos LITE",
    "[MLB] VOC Simulador de Costos": "Simulador Costos",
    "[MLB] VOC Costos": "Costos",
    "[MLB] VOC Pricing": "Pricing",
}

CONFIG_KEYS = {
    "[MLB] VOC Simulador de Costos LITE": "simulador_costos_lite",
    "[MLB] VOC Simulador de Costos": "simulador_costos",
    "[MLB] VOC Costos": "costos",
    "[MLB] VOC Pricing": "pricing",
}

DRY_RUN_DATA = pd.DataFrame(
    {
        "Seccion": ["Simulador Costos LITE", "Simulador Costos", "Costos", "Pricing"],
        "Facil %": [65.2, 71.8, 58.3, 69.4],
        "Neutro %": [20.1, 18.5, 22.7, 19.2],
        "Dificil %": [14.7, 9.7, 19.0, 11.4],
        "Respuestas": [234, 189, 156, 312],
    }
)


def _classify(score: int, scale: dict) -> str:
    if score in scale.get("easy", [4, 5]):
        return "Facil"
    if score in scale.get("neutral", [3]):
        return "Neutro"
    if score in scale.get("difficult", [1, 2]):
        return "Dificil"
    return "Sin clasificar"


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    api_token = config.get("QUALTRICS_API_TOKEN") or os.getenv("QUALTRICS_API_TOKEN")
    datacenter = config.get("QUALTRICS_DATACENTER") or os.getenv("QUALTRICS_DATACENTER")

    if not api_token or not datacenter:
        return pd.DataFrame({"Aviso": ["Configurar QUALTRICS_API_TOKEN y QUALTRICS_DATACENTER en .env"]})

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.qualtrics_client import QualtricsClient

    client = QualtricsClient(api_token, datacenter)
    surveys_config = config.get("qualtrics", {}).get("surveys", {})

    rows = []
    for name in SURVEY_NAMES:
        key = CONFIG_KEYS[name]
        sv_cfg = surveys_config.get(key, {})
        survey_id = sv_cfg.get("id")
        ces_qid = sv_cfg.get("ces_question_id")
        scale = sv_cfg.get("ces_scale", {"easy": [4, 5], "neutral": [3], "difficult": [1, 2]})
        short = SHORT_NAMES[name]

        if not survey_id or not ces_qid:
            rows.append({
                "Seccion": short,
                "Facil %": None, "Neutro %": None, "Dificil %": None,
                "Respuestas": 0,
                "Nota": "Configurar en config/surveys.yaml (ejecutar discover_surveys.py)",
            })
            continue

        try:
            df = client.export_responses(
                survey_id, params["start_date"], params["end_date"]
            )
            if ces_qid not in df.columns or df.empty:
                rows.append({
                    "Seccion": short,
                    "Facil %": None, "Neutro %": None, "Dificil %": None,
                    "Respuestas": 0, "Nota": "Sin respuestas en el periodo",
                })
                continue

            scores = pd.to_numeric(df[ces_qid], errors="coerce").dropna().astype(int)
            total = len(scores)
            if total == 0:
                rows.append({
                    "Seccion": short,
                    "Facil %": None, "Neutro %": None, "Dificil %": None,
                    "Respuestas": 0, "Nota": "Sin respuestas validas",
                })
                continue

            cats = scores.apply(lambda s: _classify(s, scale))
            rows.append({
                "Seccion": short,
                "Facil %": round(100 * (cats == "Facil").sum() / total, 1),
                "Neutro %": round(100 * (cats == "Neutro").sum() / total, 1),
                "Dificil %": round(100 * (cats == "Dificil").sum() / total, 1),
                "Respuestas": total,
            })
        except Exception as e:
            rows.append({
                "Seccion": short,
                "Facil %": None, "Neutro %": None, "Dificil %": None,
                "Respuestas": 0, "Nota": f"Error: {e}",
            })

    return pd.DataFrame(rows)
