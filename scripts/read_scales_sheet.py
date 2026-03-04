#!/usr/bin/env python3
"""
Lee el Google Sheet con las escalas de CES por survey
y actualiza config/surveys.yaml con los valores correctos.

Prerequisito:
    gcloud auth application-default login \
      --scopes=https://www.googleapis.com/auth/cloud-platform,\
https://www.googleapis.com/auth/spreadsheets.readonly

Uso:
    uv run --with-requirements scripts/requirements.txt scripts/read_scales_sheet.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SHEET_ID = "1BWaML4knSlNTYLDpkmPQSZZEZ_j-MoIi6HwB813EGwc"


def get_credentials():
    import google.auth
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return creds


def read_sheet(sheet_id: str, range_name: str = "A:Z") -> list[list]:
    from googleapiclient.discovery import build
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=range_name)
        .execute()
    )
    return result.get("values", [])


def get_all_sheets(sheet_id: str) -> list[str]:
    """Devuelve los nombres de todas las pestañas del spreadsheet."""
    from googleapiclient.discovery import build
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return [s["properties"]["title"] for s in meta.get("sheets", [])]


def main():
    print("Conectando a Google Sheets...")

    try:
        sheets = get_all_sheets(SHEET_ID)
    except Exception as e:
        print(f"ERROR: No se pudo acceder al sheet: {e}")
        print()
        print("Asegurate de haber corrido:")
        print("  gcloud auth application-default login \\")
        print("    --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/spreadsheets.readonly")
        sys.exit(1)

    print(f"Pestanas encontradas: {sheets}\n")

    # Leer todas las pestanas
    all_data = {}
    for sheet_name in sheets:
        rows = read_sheet(SHEET_ID, f"'{sheet_name}'!A:Z")
        all_data[sheet_name] = rows
        print(f"\n=== {sheet_name} ===")
        for row in rows:
            print("  ", row)

    print("\n" + "="*60)
    print("Contenido completo del sheet leido.")
    print("Revisar arriba para identificar las escalas por survey.")
    print("="*60)


if __name__ == "__main__":
    main()
