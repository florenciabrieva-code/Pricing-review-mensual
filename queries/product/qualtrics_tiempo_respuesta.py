"""
Tiempo de respuesta promedio por survey (Qualtrics)

Usa el campo 'duration' (segundos) que Qualtrics incluye en cada respuesta.
"""
import os
import sys
from pathlib import Path

import pandas as pd

TITLE = "Tiempo de respuesta - Encuestas UX"
SECTION = "product"
DESCRIPTION = "Tiempo promedio y mediana para completar cada encuesta en el mes"
ORDER = 2

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
        "Promedio (min)": [3.2, 4.1, 3.8, 5.2],
        "Mediana (min)": [2.8, 3.5, 3.2, 4.7],
        "Min (min)": [0.5, 0.8, 0.6, 1.0],
        "Max (min)": [18.3, 22.1, 19.7, 28.4],
        "Respuestas": [234, 189, 156, 312],
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

    client = QualtricsClient(api_token, datacenter)
    surveys_config = config.get("qualtrics", {}).get("surveys", {})

    rows = []
    for name in SURVEY_NAMES:
        key = CONFIG_KEYS[name]
        sv_cfg = surveys_config.get(key, {})
        survey_id = sv_cfg.get("id")
        short = SHORT_NAMES[name]

        if not survey_id:
            rows.append({
                "Seccion": short,
                "Promedio (min)": None, "Mediana (min)": None,
                "Min (min)": None, "Max (min)": None,
                "Respuestas": 0,
                "Nota": "Configurar en config/surveys.yaml",
            })
            continue

        try:
            df = client.export_responses(
                survey_id, params["start_date"], params["end_date"]
            )

            # Qualtrics expone 'duration' en segundos
            duration_col = next(
                (c for c in df.columns if c.lower() == "duration"), None
            )
            if not duration_col or df.empty:
                rows.append({
                    "Seccion": short,
                    "Promedio (min)": None, "Mediana (min)": None,
                    "Min (min)": None, "Max (min)": None,
                    "Respuestas": 0, "Nota": "Sin respuestas en el periodo",
                })
                continue

            durations = pd.to_numeric(df[duration_col], errors="coerce").dropna()
            # Filtrar outliers extremos (< 30 seg = bot, > 60 min = abandono)
            durations = durations[(durations >= 30) & (durations <= 3600)]
            durations_min = durations / 60

            rows.append({
                "Seccion": short,
                "Promedio (min)": round(durations_min.mean(), 1),
                "Mediana (min)": round(durations_min.median(), 1),
                "Min (min)": round(durations_min.min(), 1),
                "Max (min)": round(durations_min.max(), 1),
                "Respuestas": len(durations),
            })
        except Exception as e:
            rows.append({
                "Seccion": short,
                "Promedio (min)": None, "Mediana (min)": None,
                "Min (min)": None, "Max (min)": None,
                "Respuestas": 0, "Nota": f"Error: {e}",
            })

    return pd.DataFrame(rows)
