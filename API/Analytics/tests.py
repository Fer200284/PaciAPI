from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .serializers import EncuestaSerializer
from .services import guardar_encuesta
from .views import EncuestasView


ENCUESTA = {
    "id_encuesta": 1054,
    "id_fecha": "2026-10-26",
    "id_paciente": 102,
    "id_patologia": 12,
    "puntuacion_general": 5,
    "score_atencion_medica": 5,
    "tiempo_espera_minutos": 5,
    "score_trato_personal": 5,
    "score_consulta_doctor": 5,
    "resolucion_dudas_val": 1,
}


class EncuestaSerializerTests(SimpleTestCase):
    def test_accepts_iso_date_survey_payload(self):
        serializer = EncuestaSerializer(data=ENCUESTA)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["id_fecha"],
            date(2026, 10, 26),
        )

    def test_rejects_scores_outside_one_to_five(self):
        serializer = EncuestaSerializer(data={
            **ENCUESTA,
            "puntuacion_general": 6,
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("puntuacion_general", serializer.errors)

    def test_rejects_invalid_date_key(self):
        serializer = EncuestaSerializer(data={
            **ENCUESTA,
            "id_fecha": "2026-02-30",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("id_fecha", serializer.errors)

    def test_rejects_date_without_hyphens(self):
        serializer = EncuestaSerializer(data={
            **ENCUESTA,
            "id_fecha": "20261026",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("id_fecha", serializer.errors)


class EncuestaServiceTests(SimpleTestCase):
    @patch("Analytics.services.get_encuestas_collection")
    def test_saves_validated_survey_and_returns_mongo_id(self, collection):
        collection.return_value.insert_one.return_value.inserted_id = "mongo-id"
        serializer = EncuestaSerializer(data=ENCUESTA)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        result = guardar_encuesta(serializer.validated_data)

        self.assertEqual(result, "mongo-id")
        collection.return_value.insert_one.assert_called_once_with(ENCUESTA)


class EncuestasApiTests(SimpleTestCase):
    @patch("Analytics.views.guardar_encuesta", return_value="mongo-object-id")
    def test_patient_can_submit_survey(self, guardar_encuesta):
        patient = SimpleNamespace(
            is_authenticated=True,
            rol="Paciente",
        )
        request = APIRequestFactory().post(
            "/api/analytics/encuestas/",
            ENCUESTA,
            format="json",
        )
        force_authenticate(request, user=patient)

        response = EncuestasView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {"id": "mongo-object-id"})
        guardar_encuesta.assert_called_once_with({
            **ENCUESTA,
            "id_fecha": date(2026, 10, 26),
        })

    @patch("Analytics.views.guardar_encuesta")
    def test_non_patient_cannot_submit_survey(self, guardar_encuesta):
        manager = SimpleNamespace(
            is_authenticated=True,
            rol="Gerencia",
        )
        request = APIRequestFactory().post(
            "/api/analytics/encuestas/",
            ENCUESTA,
            format="json",
        )
        force_authenticate(request, user=manager)

        response = EncuestasView.as_view()(request)

        self.assertEqual(response.status_code, 403)
        guardar_encuesta.assert_not_called()
