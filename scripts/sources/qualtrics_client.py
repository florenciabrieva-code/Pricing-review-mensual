"""
Qualtrics API Client
Maneja autenticacion, export async y descarga de respuestas.
"""
import io
import time
import zipfile

import pandas as pd
import requests


class QualtricsClient:
    def __init__(self, api_token: str, datacenter: str):
        self.api_token = api_token
        self.datacenter = datacenter
        self.base_url = f"https://{datacenter}.qualtrics.com/API/v3"
        self.headers = {
            "X-API-TOKEN": api_token,
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict = None):
        r = requests.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, payload: dict):
        r = requests.post(
            f"{self.base_url}{path}",
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Survey discovery
    # ------------------------------------------------------------------

    def list_surveys(self) -> list:
        """Devuelve lista de {id, name} para todos los surveys."""
        surveys = []
        offset = 0
        while True:
            data = self._get("/surveys", params={"offset": offset})
            elements = data.get("result", {}).get("elements", [])
            if not elements:
                break
            surveys.extend({"id": s["id"], "name": s["name"]} for s in elements)
            next_page = data.get("result", {}).get("nextPage")
            if not next_page:
                break
            offset += len(elements)
        return surveys

    def find_survey_id(self, name: str) -> str | None:
        """Busca un survey por nombre exacto y devuelve su ID."""
        for s in self.list_surveys():
            if s["name"] == name:
                return s["id"]
        return None

    def get_survey_questions(self, survey_id: str) -> list:
        """Devuelve lista de {id, text, type} para todas las preguntas."""
        data = self._get(f"/surveys/{survey_id}")
        questions = []
        for qid, q in data.get("result", {}).get("questions", {}).items():
            questions.append(
                {
                    "id": qid,
                    "text": q.get("questionText", "").replace("<br>", " ").strip(),
                    "type": q.get("questionType", {}).get("type", ""),
                    "selector": q.get("questionType", {}).get("selector", ""),
                }
            )
        return questions

    # ------------------------------------------------------------------
    # Response export (async 3-step)
    # ------------------------------------------------------------------

    def export_responses(
        self,
        survey_id: str,
        start_date: str,
        end_date: str,
        use_labels: bool = False,
        question_ids: list = None,
    ) -> pd.DataFrame:
        """
        Exporta respuestas de un survey en un rango de fechas.

        Args:
            survey_id: ID del survey (SV_...)
            start_date: YYYY-MM-DD
            end_date:   YYYY-MM-DD
            use_labels: True para texto de las opciones, False para valores numericos
            question_ids: lista de QIDs a incluir (None = todos)

        Returns:
            DataFrame con todas las respuestas (sin las 2 filas de metadata de Qualtrics).
        """
        payload = {
            "format": "csv",
            "compress": True,
            "useLabels": use_labels,
            "startDate": f"{start_date}T00:00:00Z",
            "endDate": f"{end_date}T23:59:59Z",
        }
        if question_ids:
            payload["questionIds"] = question_ids

        # Paso 1: iniciar export
        resp = self._post(f"/surveys/{survey_id}/export-responses", payload)
        progress_id = resp["result"]["progressId"]

        # Paso 2: polling hasta completar
        file_id = None
        for _ in range(72):  # max ~6 min (72 x 5s)
            status = self._get(
                f"/surveys/{survey_id}/export-responses/{progress_id}"
            )
            result = status["result"]
            state = result.get("status", "")
            if state == "complete":
                file_id = result["fileId"]
                break
            elif state == "failed":
                raise RuntimeError(f"Qualtrics export failed: {result}")
            time.sleep(5)

        if not file_id:
            raise TimeoutError("Qualtrics export timed out after 6 minutes")

        # Paso 3: descargar zip y leer CSV
        r = requests.get(
            f"{self.base_url}/surveys/{survey_id}/export-responses/{file_id}/file",
            headers=self.headers,
            timeout=60,
        )
        r.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                # Qualtrics agrega 2 filas de metadata despues del header → skiprows
                df = pd.read_csv(f, skiprows=[1, 2], low_memory=False)

        return df
