#!/usr/bin/env python3
"""
Setup: Descubre Survey IDs y estructura de preguntas en Qualtrics.
Correr UNA SOLA VEZ para configurar config/surveys.yaml.

Uso:
    uv run --with-requirements scripts/requirements.txt scripts/discover_surveys.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sources.qualtrics_client import QualtricsClient

TARGET_SURVEYS = [
    "[MLB] VOC Simulador de Costos LITE",
    "[MLB] VOC Simulador de Costos",
    "[MLB] VOC Costos",
    "[MLB] VOC Pricing",
]

CONFIG_KEYS = {
    "[MLB] VOC Simulador de Costos LITE": "simulador_costos_lite",
    "[MLB] VOC Simulador de Costos": "simulador_costos",
    "[MLB] VOC Costos": "costos",
    "[MLB] VOC Pricing": "pricing",
}


def main():
    api_token = os.getenv("QUALTRICS_API_TOKEN")
    datacenter = os.getenv("QUALTRICS_DATACENTER")

    if not api_token or not datacenter:
        print("ERROR: Faltan variables de entorno:")
        print("  QUALTRICS_API_TOKEN=tu_token")
        print("  QUALTRICS_DATACENTER=fra1  (o ca1, iad1, etc.)")
        print()
        print("Agregarlas en el archivo .env del repo.")
        sys.exit(1)

    client = QualtricsClient(api_token, datacenter)

    print("Buscando surveys en Qualtrics...\n")
    all_surveys = client.list_surveys()
    print(f"Total surveys encontrados: {len(all_surveys)}\n")

    found = {}
    for name in TARGET_SURVEYS:
        match = next((s for s in all_surveys if s["name"] == name), None)
        if match:
            found[name] = match["id"]
            print(f"[OK] {name}")
            print(f"     ID: {match['id']}")
        else:
            found[name] = None
            print(f"[NO ENCONTRADO] {name}")
            similar = [s["name"] for s in all_surveys if "VOC" in s["name"] or "Pricing" in s["name"] or "Costos" in s["name"]]
            if similar:
                print(f"     Surveys similares: {similar[:5]}")
        print()

    # Mostrar preguntas de cada survey encontrado
    yaml_lines = ["qualtrics:", "  surveys:"]

    for name, survey_id in found.items():
        key = CONFIG_KEYS[name]
        short_name = name.replace("[MLB] VOC ", "")
        yaml_lines.append(f"")
        yaml_lines.append(f"    {key}:")
        yaml_lines.append(f"      name: \"{name}\"")

        if not survey_id:
            yaml_lines.append(f"      id: null  # Survey no encontrado - verificar nombre exacto")
            yaml_lines.append(f"      ces_question_id: null")
            yaml_lines.append(f"      doubts_question_id: null")
            if key == "pricing":
                yaml_lines.append(f"      awareness_question_id: null")
            yaml_lines.append(f"      ces_scale:")
            yaml_lines.append(f"        easy: [4, 5]")
            yaml_lines.append(f"        neutral: [3]")
            yaml_lines.append(f"        difficult: [1, 2]")
            continue

        yaml_lines.append(f"      id: \"{survey_id}\"")

        print(f"Preguntas de '{short_name}' ({survey_id}):")
        print("-" * 60)
        try:
            questions = client.get_survey_questions(survey_id)
            for q in questions:
                print(f"  {q['id']:10s} [{q['type']:10s}] {q['text'][:80]}")
            print()

            # Detectar Q1 (probablemente CES) y preguntas de texto abierto
            q1 = next((q for q in questions if q["id"] == "QID1"), None)
            open_text_qs = [q for q in questions if q.get("selector") in ("ESTB", "ESSAY") or q["type"] == "TE"]

            ces_qid = q1["id"] if q1 else (questions[0]["id"] if questions else "QID1")
            doubts_qid = open_text_qs[0]["id"] if open_text_qs else "QID2"

            yaml_lines.append(f"      ces_question_id: \"{ces_qid}\"  # {(q1 or {}).get('text', '')[:60]}")
            yaml_lines.append(f"      doubts_question_id: \"{doubts_qid}\"  # Texto abierto - verificar")
            if key == "pricing":
                awareness_q = questions[-1] if questions else {"id": "QID_X"}
                yaml_lines.append(f"      awareness_question_id: \"{awareness_q['id']}\"  # Verificar cual es la pregunta de awareness")
            yaml_lines.append(f"      ces_scale:")
            yaml_lines.append(f"        easy: [4, 5]   # Ajustar segun escala real del survey (1-5 o 1-7)")
            yaml_lines.append(f"        neutral: [3]")
            yaml_lines.append(f"        difficult: [1, 2]")

        except Exception as e:
            print(f"  ERROR al obtener preguntas: {e}\n")
            yaml_lines.append(f"      ces_question_id: null  # Error: {e}")
            yaml_lines.append(f"      doubts_question_id: null")

    # Escribir YAML
    output = ROOT / "config" / "surveys.yaml"
    output.parent.mkdir(exist_ok=True)
    output.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    print("=" * 60)
    print(f"config/surveys.yaml generado: {output}")
    print()
    print("PROXIMOS PASOS:")
    print("1. Revisar config/surveys.yaml")
    print("2. Verificar que ces_question_id sea la pregunta de facilidad de uso (Q1)")
    print("3. Verificar que doubts_question_id sea la pregunta de texto abierto de dudas")
    if "[MLB] VOC Pricing" in found:
        print("4. Verificar awareness_question_id en la seccion 'pricing'")
    print("5. Ajustar ces_scale si la escala no es 1-5")
    print()
    print("Luego correr: generar_reporte.bat 2026 3")


if __name__ == "__main__":
    main()
