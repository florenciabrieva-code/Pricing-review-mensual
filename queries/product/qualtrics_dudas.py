"""
Principales dudas por seccion (Google Sheets + AI)

Lee respuestas de texto abierto / multi-choice desde Google Sheets
y usa Claude para agruparlas en categorias tematicas con % de representatividad.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

TITLE = "Principales dudas por seccion"
SECTION = "product"
DESCRIPTION = "Categorias de dudas identificadas en las encuestas, ordenadas por representatividad"
ORDER = 3

SURVEY_ORDER = ["simulador_costos_lite", "simulador_costos", "costos", "pricing"]
SHORT_NAMES = {
    "simulador_costos_lite": "Simulador Costos LITE",
    "simulador_costos":      "Simulador Costos",
    "costos":                "Costos",
    "pricing":               "Pricing",
}

DRY_RUN_DATA = pd.DataFrame({
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
})


def _collect_responses(df: pd.DataFrame, sv_cfg: dict) -> list[str]:
    """Extrae lista de respuestas de texto segun el tipo de pregunta del survey."""
    doubts_col = sv_cfg.get("doubts_column")
    doubts_type = sv_cfg.get("doubts_type", "text")

    if not doubts_col or doubts_col not in df.columns:
        return []

    if doubts_type == "text":
        responses = (
            df[doubts_col]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s.str.len() > 5]
            .tolist()
        )
    else:  # multichoice: cada fila puede tener varias opciones separadas por coma
        raw = df[doubts_col].dropna().astype(str).str.strip()
        responses = []
        for val in raw:
            if val and len(val) > 2:
                # Cada opcion seleccionada va separada por coma en el export
                for part in val.split(","):
                    part = part.strip()
                    if part and len(part) > 3:
                        responses.append(part)
        # Agregar campo "Otro" si existe
        other_col = sv_cfg.get("doubts_other_column")
        if other_col and other_col in df.columns:
            others = (
                df[other_col]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[lambda s: s.str.len() > 5]
                .tolist()
            )
            responses.extend(others)

    return responses


def _categorize_with_ai(responses: list[str], section_name: str, api_key: str) -> list[dict]:
    """Usa Claude para agrupar respuestas en categorias tematicas."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    sample = responses[:300]
    text = "\n".join(f"- {r}" for r in sample)

    prompt = f"""Sos un analista de UX revisando respuestas de una encuesta sobre "{section_name}" de Mercado Pago.

Hay {len(sample)} respuestas de usuarios describiendo sus dudas o comentarios (en portugues).

Tu tarea:
1. Identificar entre 5 y 8 categorias tematicas principales
2. Contar cuantas respuestas pertenecen a cada categoria
3. Calcular el porcentaje sobre el total

Responde UNICAMENTE con JSON valido, sin texto adicional:
[
  {{"categoria": "Nombre de la categoria", "cantidad": 45, "porcentaje": 19.2}},
  ...
]

Respuestas:
{text}"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    start, end = raw.find("["), raw.rfind("]") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]
    return json.loads(raw)


def run(params: dict, config: dict, dry_run: bool = False) -> pd.DataFrame:
    if dry_run:
        return DRY_RUN_DATA

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from sources.sheets_reader import SheetsReader

    reader = SheetsReader()
    surveys_cfg = config.get("qualtrics", {}).get("surveys", {})
    anthropic_key = config.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    all_rows = []
    for key in SURVEY_ORDER:
        sv = surveys_cfg.get(key, {})
        tab = sv.get("sheets_tab")
        short = SHORT_NAMES[key]

        if not tab:
            all_rows.append({"Seccion": short, "Categoria": "sheets_tab no configurado",
                             "Respuestas": None, "% del total": None})
            continue

        try:
            df = reader.get_survey_data(tab, params["start_date"], params["end_date"])
            if df.empty:
                all_rows.append({"Seccion": short, "Categoria": "Sin respuestas en el periodo",
                                 "Respuestas": 0, "% del total": None})
                continue

            responses = _collect_responses(df, sv)
            if not responses:
                all_rows.append({"Seccion": short, "Categoria": "Sin respuestas de texto",
                                 "Respuestas": 0, "% del total": None})
                continue

            if not anthropic_key:
                all_rows.append({
                    "Seccion": short,
                    "Categoria": f"{len(responses)} respuestas (agregar ANTHROPIC_API_KEY en .env para auto-categorizar)",
                    "Respuestas": len(responses), "% del total": 100.0,
                })
                continue

            categories = _categorize_with_ai(responses, short, anthropic_key)
            for cat in categories:
                all_rows.append({
                    "Seccion":     short,
                    "Categoria":   cat.get("categoria", ""),
                    "Respuestas":  cat.get("cantidad", 0),
                    "% del total": cat.get("porcentaje", 0.0),
                })

        except Exception as e:
            all_rows.append({"Seccion": short, "Categoria": f"Error: {e}",
                             "Respuestas": None, "% del total": None})

    return pd.DataFrame(all_rows)
