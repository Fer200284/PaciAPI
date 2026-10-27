from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .serializers import EncuestaSerializer
from .services import guardar_encuesta
from .views import EncuestaDetalleView, EncuestasView
from bson import ObjectId


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
    "comentario": "La atención fue muy buena.",
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

    def test_comment_is_optional(self):
        encuesta = {
            key: value
            for key, value in ENCUESTA.items()
            if key != "comentario"
        }
        serializer = EncuestaSerializer(data=encuesta)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("comentario", serializer.validated_data)

    def test_rejects_comment_longer_than_2000_characters(self):
        serializer = EncuestaSerializer(data={
            **ENCUESTA,
            "comentario": "a" * 2001,
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("comentario", serializer.errors)

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
    @patch("Analytics.views.Pacientes.objects.filter")
    @patch("Analytics.views.listar_encuestas")
    def test_patient_lists_only_surveys_for_linked_profile(
        self,
        listar,
        pacientes,
    ):
        patient = SimpleNamespace(is_authenticated=True, rol="Paciente")
        object_id = ObjectId("671d45a201b2c00000000001")
        pacientes.return_value.values_list.return_value.first.return_value = 102
        listar.return_value = [{
            "_id": object_id,
            "id_paciente": 102,
            "comentario": "Atención amable.",
        }]
        request = APIRequestFactory().get("/api/analytics/encuestas/")
        force_authenticate(request, user=patient)

        response = EncuestasView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["id"], str(object_id))
        self.assertEqual(response.data[0]["id_paciente"], 102)
        listar.assert_called_once_with({"id_paciente": 102})

    @patch("Analytics.views.listar_encuestas")
    def test_gerencia_lists_all_surveys(self, listar):
        manager = SimpleNamespace(is_authenticated=True, rol="Gerencia")
        listar.return_value = []
        request = APIRequestFactory().get("/api/analytics/encuestas/")
        force_authenticate(request, user=manager)

        response = EncuestasView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        listar.assert_called_once_with({})

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

    @patch("Analytics.views.Pacientes.objects.filter")
    @patch("Analytics.views.obtener_encuesta")
    def test_patient_gets_only_own_survey(self, obtener, pacientes):
        patient = SimpleNamespace(is_authenticated=True, rol="Paciente")
        object_id = ObjectId("671d45a201b2c00000000002")
        pacientes.return_value.values_list.return_value.first.return_value = 102
        obtener.return_value = {
            "_id": object_id,
            "id_paciente": 102,
            "comentario": "Atención amable.",
        }
        request = APIRequestFactory().get(
            f"/api/analytics/encuestas/{object_id}/"
        )
        force_authenticate(request, user=patient)

        response = EncuestaDetalleView.as_view()(request, encuesta_id=str(object_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(object_id))
        obtener.assert_called_once_with({
            "_id": object_id,
            "id_paciente": 102,
        })

    @patch("Analytics.views.Pacientes.objects.filter")
    @patch("Analytics.views.actualizar_encuesta")
    @patch("Analytics.views.obtener_encuesta")
    def test_patient_updates_own_survey(
        self,
        obtener,
        actualizar,
        pacientes,
    ):
        patient = SimpleNamespace(is_authenticated=True, rol="Paciente")
        object_id = ObjectId("671d45a201b2c00000000003")
        pacientes.return_value.values_list.return_value.first.return_value = 102
        actualizar.return_value.matched_count = 1
        obtener.return_value = {
            "_id": object_id,
            "id_paciente": 102,
            "puntuacion_general": 4,
        }
        request = APIRequestFactory().patch(
            f"/api/analytics/encuestas/{object_id}/",
            {"puntuacion_general": 4},
            format="json",
        )
        force_authenticate(request, user=patient)

        response = EncuestaDetalleView.as_view()(
            request,
            encuesta_id=str(object_id),
        )

        self.assertEqual(response.status_code, 200)
        actualizar.assert_called_once_with(
            {"_id": object_id, "id_paciente": 102},
            {"puntuacion_general": 4},
        )

    @patch("Analytics.views.Pacientes.objects.filter")
    @patch("Analytics.views.eliminar_encuesta")
    def test_patient_deletes_own_survey(self, eliminar, pacientes):
        patient = SimpleNamespace(is_authenticated=True, rol="Paciente")
        object_id = ObjectId("671d45a201b2c00000000004")
        pacientes.return_value.values_list.return_value.first.return_value = 102
        eliminar.return_value.deleted_count = 1
        request = APIRequestFactory().delete(
            f"/api/analytics/encuestas/{object_id}/"
        )
        force_authenticate(request, user=patient)

        response = EncuestaDetalleView.as_view()(
            request,
            encuesta_id=str(object_id),
        )

        self.assertEqual(response.status_code, 204)
        eliminar.assert_called_once_with({
            "_id": object_id,
            "id_paciente": 102,
        })

    @patch("Analytics.views.actualizar_encuesta")
    def test_gerencia_cannot_update_survey(self, actualizar):
        manager = SimpleNamespace(is_authenticated=True, rol="Gerencia")
        object_id = ObjectId("671d45a201b2c00000000005")
        request = APIRequestFactory().patch(
            f"/api/analytics/encuestas/{object_id}/",
            {"puntuacion_general": 4},
            format="json",
        )
        force_authenticate(request, user=manager)

        response = EncuestaDetalleView.as_view()(
            request,
            encuesta_id=str(object_id),
        )

        self.assertEqual(response.status_code, 403)
        actualizar.assert_not_called()

    @patch("Analytics.views.eliminar_encuesta")
    def test_gerencia_cannot_delete_survey(self, eliminar):
        manager = SimpleNamespace(is_authenticated=True, rol="Gerencia")
        object_id = ObjectId("671d45a201b2c00000000006")
        request = APIRequestFactory().delete(
            f"/api/analytics/encuestas/{object_id}/"
        )
        force_authenticate(request, user=manager)

        response = EncuestaDetalleView.as_view()(
            request,
            encuesta_id=str(object_id),
        )

        self.assertEqual(response.status_code, 403)
        eliminar.assert_not_called()

    @patch("Analytics.views.obtener_encuesta")
    def test_invalid_mongo_id_returns_not_found_without_query(self, obtener):
        manager = SimpleNamespace(is_authenticated=True, rol="Gerencia")
        request = APIRequestFactory().get(
            "/api/analytics/encuestas/no-es-object-id/"
        )
        force_authenticate(request, user=manager)

        response = EncuestaDetalleView.as_view()(
            request,
            encuesta_id="no-es-object-id",
        )

        self.assertEqual(response.status_code, 404)
        obtener.assert_not_called()
