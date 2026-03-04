"""
Google Sheets Reader para datos de Qualtrics exportados.
Lee las pestanas de datos del spreadsheet de UX metrics y filtra por rango de fechas.
"""
import re
import unicodedata
from functools import lru_cache

import pandas as pd


SHEET_ID = "1BWaML4knSlNTYLDpkmPQSZZEZ_j-MoIi6HwB813EGwc"


def _build_service():
    import google.auth
    from googleapiclient.discovery import build

    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


class SheetsReader:
    def __init__(self):
        self._service = _build_service()

    def read_tab(self, tab_name: str) -> pd.DataFrame:
        """Lee una pestana completa y devuelve DataFrame con headers de la fila 1."""
        result = (
            self._service.spreadsheets()
            .values()
            .get(spreadsheetId=SHEET_ID, range=f"'{tab_name}'!A:S")
            .execute()
        )
        rows = result.get("values", [])
        if not rows:
            return pd.DataFrame()

        # Fila 0 = nombres cortos (Q1, Q2, StartDate...)
        # Fila 1 = descripcion larga de la pregunta
        # Fila 2 = ImportIds ({"ImportId":"QID..."})
        # Fila 3+ = datos reales
        if len(rows) < 4:
            return pd.DataFrame()

        headers = rows[0]
        data_rows = rows[3:]

        # Normalizar largo de filas
        padded = [row + [""] * max(0, len(headers) - len(row)) for row in data_rows]
        df = pd.DataFrame(padded, columns=headers)
        return df

    def get_survey_data(self, tab_name: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Lee los datos de un survey y filtra por rango de fechas.

        Args:
            tab_name:   nombre de la pestana (ej: "Datos pricing models")
            start_date: YYYY-MM-DD
            end_date:   YYYY-MM-DD

        Returns:
            DataFrame filtrado por el periodo. Columnas importantes:
            - Q1: respuesta CES (texto con emoji, ej: "Fácil")
            - Q2, Q3: preguntas adicionales segun survey
            - Duration (in seconds): duracion
            - StartDate: fecha de inicio
        """
        df = self.read_tab(tab_name)
        if df.empty or "StartDate" not in df.columns:
            return df

        # Filtrar solo respuestas completadas
        if "Finished" in df.columns:
            df = df[df["Finished"].str.lower().isin(["verdadero", "true", "1"])]

        # Excluir previews/tests
        if "Status" in df.columns:
            df = df[~df["Status"].str.lower().isin(["vista previa de encuesta", "survey preview"])]

        # Filtrar por fecha
        df["_start"] = pd.to_datetime(df["StartDate"], errors="coerce")
        df = df[
            (df["_start"] >= pd.Timestamp(start_date))
            & (df["_start"] <= pd.Timestamp(end_date + " 23:59:59"))
        ].copy()
        df.drop(columns=["_start"], inplace=True)

        return df.reset_index(drop=True)


# ------------------------------------------------------------------
# CES label classification
# ------------------------------------------------------------------

def _normalize(s: str) -> str:
    """Elimina emojis, acentos y pasa a minusculas para comparacion."""
    s = unicodedata.normalize("NFKD", str(s))
    s = re.sub(r"[^\x00-\x7F]", "", s)   # eliminar no-ASCII (emojis, acentos)
    return s.lower().strip()


def classify_ces(label: str) -> str:
    """
    Clasifica una etiqueta CES en portugues a Facil / Neutro / Dificil.

    Maneja variantes con emojis:
      '😥 Muito difícil' → Dificil
      '😐 Nem difícil nem fácil' → Neutro
      '😊 Fácil' / '😁 Muito fácil' → Facil
    """
    norm = _normalize(label)
    if not norm:
        return "Sin clasificar"
    # Orden: primero el caso neutro porque contiene tanto "dif" como "facil"
    if "nem" in norm:
        return "Neutro"
    if "dificil" in norm or "dificl" in norm:
        return "Dificil"
    if "facil" in norm or "facl" in norm:
        return "Facil"
    return "Sin clasificar"
