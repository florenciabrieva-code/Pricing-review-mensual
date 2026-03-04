"""
Principales dudas por seccion (Qualtrics + AI)

Toma las respuestas de texto abierto del mes, las agrupa con Claude
y devuelve las categorias principales con % de representatividad.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

TITLE = "Principales dudas por seccion"
SECTION = "product"
DESCRIPTION = "Categorias de dudas identificadas en texto abierto, ordenadas por representatividad"
ORDER = 3

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
        "Seccion": [
            "Simulador Costos LITE", "Simulador Costos LITE", "Simulador Costos LITE",
            "Costos", "Costos", "Costos",
            "Pricing", "Pricing",
        ],
        "Categoria": [
            "Dudas sobre comisiones por venta",
            "Como se calcula el costo de envio",
            "Diferencia entre planes de suscripcion",
            "Cuando se acredita el dinero",
            "Costos de retiro/transferencia",
            "Impuestos y retenciones",
            "Desconocia la seccion de pricing",
            "Como se actualiza el precio sugerido",
        ],
        "Respuestas": [45, 38, 22, 31, 27, 19, 58, 34],
        "% del total": [19.2, 16.2, 9.4, 19.9, 17.3, 12.2, 18.6, 10.9],
    }
)


def _categorize_with_ai(responses: list[str], section_name: str, api_key: str) -> list[dict]:
    """Usa Claude para agrupar respuestas en categorias tematicas."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # Limitar a 300 respuestas para no exceder tokens
    sample = responses[:300]
    responses_text = "\n".join(f"- {r}" for r in sample if r and str(r).strip())

    prompt = f"""Sos un analista de UX revisando respuestas abiertas de una encuesta sobre la seccion "{section_name}" de Mercado Pago.

A continuacion hay {len(sample)} respuestas de usuarios describiendo sus dudas o comentarios.

Tu tarea:
1. Identificar entre 5 y 8 categorias tematicas principales
2. Clasificar cuantas respuestas pertenecen a cada categoria
3. Calcular el porcentaje de cada categoria sobre el total

Responde UNICAMENTE con un JSON valido, sin texto adicional, con este formato exacto:
[
  {{"categoria": "Nombre de la categoria", "cantidad": 45, "porcentaje": 19.2}},
  ...
]

Respuestas de usuarios:
{responses_text}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Extraer JSON si viene con texto alrededor
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]

    return json.loads(raw)


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    api_token = config.get("QUALTRICS_API_TOKEN") or os.getenv("QUALTRICS_API_TOKEN")
    datacenter = config.get("QUALTRICS_DATACENTER") or os.getenv("QUALTRICS_DATACENTER")
    anthropic_key = config.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_token or not datacenter:
        return pd.DataFrame({"Aviso": ["Configurar QUALTRICS_API_TOKEN y QUALTRICS_DATACENTER en .env"]})

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.qualtrics_client import QualtricsClient

    client = QualtricsClient(api_token, datacenter)
    surveys_config = config.get("qualtrics", {}).get("surveys", {})

    all_rows = []

    for name in SURVEY_NAMES:
        key = CONFIG_KEYS[name]
        sv_cfg = surveys_config.get(key, {})
        survey_id = sv_cfg.get("id")
        doubts_qid = sv_cfg.get("doubts_question_id")
        short = SHORT_NAMES[name]

        if not survey_id or not doubts_qid:
            all_rows.append({
                "Seccion": short,
                "Categoria": "Configurar doubts_question_id en config/surveys.yaml",
                "Respuestas": None,
                "% del total": None,
            })
            continue

        try:
            df = client.export_responses(
                survey_id, params["start_date"], params["end_date"]
            )

            if doubts_qid not in df.columns or df.empty:
                all_rows.append({
                    "Seccion": short,
                    "Categoria": "Sin respuestas en el periodo",
                    "Respuestas": 0,
                    "% del total": None,
                })
                continue

            responses = (
                df[doubts_qid]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[lambda s: s.str.len() > 5]
                .tolist()
            )

            if not responses:
                all_rows.append({
                    "Seccion": short,
                    "Categoria": "Sin respuestas de texto en el periodo",
                    "Respuestas": 0,
                    "% del total": None,
                })
                continue

            if not anthropic_key:
                # Sin AI: mostrar conteo raw sin categorizar
                all_rows.append({
                    "Seccion": short,
                    "Categoria": f"{len(responses)} respuestas sin categorizar (configurar ANTHROPIC_API_KEY para auto-categorizacion)",
                    "Respuestas": len(responses),
                    "% del total": 100.0,
                })
                continue

            categories = _categorize_with_ai(responses, short, anthropic_key)
            for cat in categories:
                all_rows.append({
                    "Seccion": short,
                    "Categoria": cat.get("categoria", ""),
                    "Respuestas": cat.get("cantidad", 0),
                    "% del total": cat.get("porcentaje", 0.0),
                })

        except Exception as e:
            all_rows.append({
                "Seccion": short,
                "Categoria": f"Error: {e}",
                "Respuestas": None,
                "% del total": None,
            })

    return pd.DataFrame(all_rows)
