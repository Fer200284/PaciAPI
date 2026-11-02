from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from .models import Citas
from .services import registrar_llegada_cita, sincronizar_cita_proxima
from .Api.serializers import CitasSerializer


class CitasSerializerTests(SimpleTestCase):
    def test_catalog_fields_are_read_only(self):
        serializer = CitasSerializer()

        self.assertTrue(all(
            field.read_only for field in serializer.fields.values()
        ))


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

    @patch("apps.catalogos.Citas.services.Citas.objects.filter")
    def test_marks_nearest_same_day_programmed_appointment_attended(
        self,
        filter_citas,
    ):
        llegada = timezone.make_aware(
            datetime(2026, 11, 12, 9, 35),
            timezone.get_current_timezone(),
        )
        self.atencion.fecha_atencion = date(2026, 11, 12)
        cita = SimpleNamespace(
            fecha_hora_cita=timezone.make_aware(
                datetime(2026, 11, 12, 9, 30),
                timezone.get_current_timezone(),
            ),
            estado=Citas.Estado.PROGRAMADA,
            fecha_atencion_real=None,
            save=Mock(),
        )
        filter_citas.return_value = [cita]

        resultado = registrar_llegada_cita(self.atencion, llegada)

        self.assertIs(resultado, cita)
        self.assertEqual(cita.estado, Citas.Estado.ASISTIO)
        self.assertEqual(cita.fecha_atencion_real, llegada)
        cita.save.assert_called_once_with(
            update_fields=["estado", "fecha_atencion_real"]
        )

    @patch("apps.catalogos.Citas.services.Citas.objects.filter")
    def test_does_not_change_appointment_when_there_is_no_match(
        self,
        filter_citas,
    ):
        self.atencion.fecha_atencion = date(2026, 11, 12)
        filter_citas.return_value = []

        self.assertIsNone(registrar_llegada_cita(
            self.atencion,
            timezone.now(),
        ))
