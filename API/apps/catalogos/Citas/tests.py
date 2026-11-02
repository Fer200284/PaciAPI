from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from .models import Citas
from .services import sincronizar_cita_proxima
from .Api.serializers import CitasSerializer
from .Api.views import CitasViewSet


class CitasSerializerTests(SimpleTestCase):
    def test_catalog_fields_are_read_only(self):
        serializer = CitasSerializer()

        self.assertTrue(all(
            field.read_only for field in serializer.fields.values()
        ))


class CitasViewSetTests(SimpleTestCase):
    @patch("apps.catalogos.Citas.Api.views.timezone.now")
    def test_lists_only_future_programmed_appointments(self, now):
        instante = timezone.make_aware(
            datetime(2026, 11, 12, 9, 0),
            timezone.get_current_timezone(),
        )
        now.return_value = instante
        queryset = Mock()
        view = CitasViewSet()
        view.queryset = queryset
        view.request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, rol="Administrador")
        )

        view.get_queryset()

        queryset.filter.assert_called_once_with(
            estado=Citas.Estado.PROGRAMADA,
            fecha_hora_cita__gt=instante,
        )


class SincronizarCitaProximaTests(SimpleTestCase):
    def setUp(self):
        self.atencion = SimpleNamespace(
            id_paciente_patologia=SimpleNamespace(id_paciente_id=14),
            id_medico_id=6,
            fecha_proxima_cita=date(2026, 11, 12),
            hora_proxima_cita=time(9, 30),
            observaciones="Control de seguimiento",
        )

    @patch("apps.catalogos.Citas.services.Citas.objects.filter")
    @patch("apps.catalogos.Citas.services.Citas.objects.create")
    def test_creates_only_required_scheduled_appointment_fields(
        self,
        create,
        filter_citas,
    ):
        filter_citas.return_value.order_by.return_value.first.return_value = None
        create.return_value = Mock()
        esperado = timezone.make_aware(
            datetime(2026, 11, 12, 9, 30),
            timezone.get_current_timezone(),
        )

        sincronizar_cita_proxima(self.atencion)

        create.assert_called_once_with(
            id_paciente_id=14,
            id_medico_id=6,
            fecha_hora_cita=esperado,
            estado=Citas.Estado.PROGRAMADA,
            observaciones="Control de seguimiento",
        )

    @patch("apps.catalogos.Citas.services.Citas.objects.filter")
    def test_updates_existing_programmed_appointment(self, filter_citas):
        anterior = {
            "fecha_anterior": date(2026, 11, 10),
            "hora_anterior": time(8, 0),
            "paciente_anterior_id": 14,
            "medico_anterior_id": 6,
        }
        cita = Mock()
        filter_citas.return_value.order_by.return_value.first.return_value = cita

        resultado = sincronizar_cita_proxima(self.atencion, **anterior)

        self.assertIs(resultado, cita)
        self.assertEqual(cita.fecha_hora_cita.date(), date(2026, 11, 12))
        cita.save.assert_called_once_with(update_fields=[
            "id_paciente",
            "id_medico",
            "fecha_hora_cita",
            "observaciones",
        ])

    @patch("apps.catalogos.Citas.services.Citas.objects.filter")
    @patch("apps.catalogos.Citas.services.Citas.objects.create")
    def test_truncates_observations_to_catalog_field_limit(
        self,
        create,
        filter_citas,
    ):
        filter_citas.return_value.order_by.return_value.first.return_value = None
        self.atencion.observaciones = "a" * 700

        sincronizar_cita_proxima(self.atencion)

        self.assertEqual(
            create.call_args.kwargs["observaciones"],
            "a" * 500,
        )

    @patch("apps.catalogos.Citas.services.Citas.objects.filter")
    def test_cancels_linked_programmed_appointment_when_schedule_cleared(
        self,
        filter_citas,
    ):
        anterior = {
            "fecha_anterior": date(2026, 11, 10),
            "hora_anterior": time(8, 0),
            "paciente_anterior_id": 14,
            "medico_anterior_id": 6,
        }
        self.atencion.fecha_proxima_cita = None
        self.atencion.hora_proxima_cita = None
        cita = Mock()
        filter_citas.return_value.order_by.return_value.first.return_value = cita

        resultado = sincronizar_cita_proxima(self.atencion, **anterior)

        self.assertIs(resultado, cita)
        self.assertEqual(cita.estado, Citas.Estado.CANCELADA)
        cita.save.assert_called_once_with(update_fields=["estado"])
