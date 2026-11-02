from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.db.models.deletion import ProtectedError
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from .Api.views import (
    AnalyticsStorageUnavailable,
    AtencionCronicoViewSet,
    AtencionHasRelatedRecords,
)
from .Api.serializers import AtencionCronicoSerializer


class AtencionCronicoSerializerTests(SimpleTestCase):
    def test_requires_time_when_next_appointment_date_is_set(self):
        serializer = AtencionCronicoSerializer(
            data={"fecha_proxima_cita": "2026-11-12"},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("hora_proxima_cita", serializer.errors)

    def test_accepts_next_appointment_with_date_and_time(self):
        serializer = AtencionCronicoSerializer(
            data={
                "fecha_proxima_cita": "2026-11-12",
                "hora_proxima_cita": "09:30:00",
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)


class AtencionCronicoViewSetTests(SimpleTestCase):
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.guardar_atencion_desde_modelo"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    @patch.object(AtencionCronicoViewSet, "get_object")
    @patch.object(AtencionCronicoViewSet, "get_serializer")
    def test_staff_finalizes_consultation_and_returns_saved_timestamp(
        self,
        get_serializer,
        get_object,
        atomic,
        guardar_analitica,
    ):
        atencion = Mock()
        atencion.fecha_hora_inicio_consulta = object()
        atencion.fecha_hora_fin_consulta = None
        get_object.return_value = atencion
        get_serializer.return_value.data = {
            "fecha_hora_fin_consulta": "2026-10-28T10:25:00-06:00",
        }
        staff = SimpleNamespace(is_authenticated=True, rol="Administrador")
        request = APIRequestFactory().post(
            "/api/atencion-cronico/28/finalizar-consulta/",
            {},
            format="json",
        )
        force_authenticate(request, user=staff)

        response = AtencionCronicoViewSet.as_view(
            {"post": "finalizar_consulta"}
        )(request, pk="28")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["fecha_hora_fin_consulta"],
            "2026-10-28T10:25:00-06:00",
        )
        self.assertIsNotNone(atencion.fecha_hora_fin_consulta)
        atencion.save.assert_called_once_with(
            update_fields=["fecha_hora_fin_consulta"]
        )
        guardar_analitica.assert_called_once_with(atencion)

    @patch(
        "apps.catalogos.Atención_cronico.Api.views.eliminar_atencion"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_delete_removes_analytics_document(
        self,
        atomic,
        eliminar_analitica,
    ):
        atencion = Mock()
        atencion.pk = 28
        view = AtencionCronicoViewSet()

        view.perform_destroy(atencion)

        atencion.delete.assert_called_once_with()
        eliminar_analitica.assert_called_once_with(28)

    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_delete_reports_when_related_records_block_it(self, atomic):
        atencion = Mock()
        atencion.delete.side_effect = ProtectedError("blocked", [])
        view = AtencionCronicoViewSet()

        with self.assertRaises(AtencionHasRelatedRecords) as context:
            view.perform_destroy(atencion)

        self.assertEqual(context.exception.status_code, 409)

    @patch(
        "apps.catalogos.Atención_cronico.Api.views.guardar_atencion_desde_modelo"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    @patch.object(AtencionCronicoViewSet, "get_object")
    @patch.object(AtencionCronicoViewSet, "get_serializer")
    def test_patient_marks_arrival_and_syncs_it(
        self,
        get_serializer,
        get_object,
        atomic,
        guardar_analitica,
    ):
        atencion = Mock()
        atencion.fecha_hora_llegada = None
        atencion.asistio = False
        get_object.return_value = atencion
        get_serializer.return_value.data = {
            "fecha_hora_llegada": "2026-10-28T10:00:00-06:00",
        }
        patient = SimpleNamespace(is_authenticated=True, rol="Paciente")
        request = APIRequestFactory().post(
            "/api/atencion-cronico/28/marcar-llegada/",
            {},
            format="json",
        )
        force_authenticate(request, user=patient)

        response = AtencionCronicoViewSet.as_view(
            {"post": "marcar_llegada"}
        )(request, pk="28")

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(atencion.fecha_hora_llegada)
        self.assertTrue(atencion.asistio)
        atencion.save.assert_called_once_with(
            update_fields=["fecha_hora_llegada", "asistio"]
        )
        guardar_analitica.assert_called_once_with(atencion)

    @patch.object(AtencionCronicoViewSet, "get_object")
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_cannot_start_consultation_before_arrival(
        self,
        atomic,
        get_object,
    ):
        atencion = SimpleNamespace(
            fecha_hora_inicio_consulta=None,
            fecha_hora_llegada=None,
        )
        get_object.return_value = atencion
        admin = SimpleNamespace(is_authenticated=True, rol="Administrador")
        request = APIRequestFactory().post(
            "/api/atencion-cronico/28/iniciar-consulta/",
            {},
            format="json",
        )
        force_authenticate(request, user=admin)
        request.user = admin
        view = AtencionCronicoViewSet()
        view.request = request

        with self.assertRaises(ValidationError) as context:
            view._registrar_momento(
                request,
                28,
                "fecha_hora_inicio_consulta",
                requiere="fecha_hora_llegada",
            )

        self.assertEqual(context.exception.status_code, 400)

    @patch(
        "apps.catalogos.Atención_cronico.Api.views.guardar_atencion_desde_modelo"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.sincronizar_cita_proxima"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_create_saves_analytics_document_after_operational_record(
        self,
        atomic,
        sincronizar_cita,
        guardar_analitica,
    ):
        atencion = SimpleNamespace(pk=28)
        serializer = Mock()
        serializer.instance = atencion
        view = AtencionCronicoViewSet()

        view.perform_create(serializer)

        serializer.save.assert_called_once_with()
        sincronizar_cita.assert_called_once_with(atencion)
        guardar_analitica.assert_called_once_with(atencion)

    @patch(
        "apps.catalogos.Atención_cronico.Api.views.guardar_atencion_desde_modelo"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.sincronizar_cita_proxima"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_update_synchronizes_edited_operational_record(
        self,
        atomic,
        sincronizar_cita,
        guardar_analitica,
    ):
        atencion = SimpleNamespace(
            pk=28,
            fecha_proxima_cita=None,
            hora_proxima_cita=None,
            id_paciente_patologia=SimpleNamespace(id_paciente_id=102),
            id_medico_id=14,
        )
        serializer = Mock()
        serializer.instance = atencion
        view = AtencionCronicoViewSet()

        view.perform_update(serializer)

        serializer.save.assert_called_once_with()
        sincronizar_cita.assert_called_once_with(
            atencion,
            fecha_anterior=None,
            hora_anterior=None,
            paciente_anterior_id=102,
            medico_anterior_id=14,
        )
        guardar_analitica.assert_called_once_with(atencion)

    @patch(
        "apps.catalogos.Atención_cronico.Api.views.guardar_atencion_desde_modelo"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.sincronizar_cita_proxima"
    )
    @patch(
        "apps.catalogos.Atención_cronico.Api.views.transaction.atomic",
        return_value=nullcontext(),
    )
    def test_create_fails_explicitly_when_analytics_storage_is_unavailable(
        self,
        atomic,
        sincronizar_cita,
        guardar_analitica,
    ):
        guardar_analitica.side_effect = ImproperlyConfigured(
            "MongoDB is not configured"
        )
        serializer = Mock()
        serializer.instance = SimpleNamespace(pk=28)
        view = AtencionCronicoViewSet()

        with self.assertRaises(AnalyticsStorageUnavailable) as context:
            view.perform_create(serializer)

        self.assertEqual(context.exception.status_code, 503)
