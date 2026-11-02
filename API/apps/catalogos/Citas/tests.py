from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.db.models import Q
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

    def test_includes_tracking_data_from_linked_attention(self):
        llegada = timezone.now()
        inicio = llegada + timedelta(minutes=5)
        atencion = SimpleNamespace(
            pk=12,
            fecha_hora_llegada=llegada,
            fecha_hora_inicio_consulta=inicio,
            fecha_hora_fin_consulta=None,
        )
        cita = SimpleNamespace(_atenciones_cita=[atencion])
        serializer = CitasSerializer()

        self.assertEqual(serializer.get_id_atencion(cita), 12)
        self.assertEqual(serializer.get_fecha_hora_llegada(cita), llegada)
        self.assertEqual(
            serializer.get_fecha_hora_inicio_consulta(cita),
            inicio,
        )
        self.assertIsNone(serializer.get_fecha_hora_fin_consulta(cita))

    @patch("apps.catalogos.Citas.Api.serializers.AtencionCronico.objects.filter")
    def test_resolves_appointments_without_a_saved_foreign_key(self, filter_atenciones):
        fecha_hora = timezone.make_aware(
            datetime(2026, 11, 12, 9, 30),
            timezone.get_current_timezone(),
        )
        cita = SimpleNamespace(
            fecha_hora_cita=fecha_hora,
            id_paciente_id=14,
            id_medico_id=6,
            _atenciones_cita=[],
        )
        atencion = SimpleNamespace(pk=22)
        filter_atenciones.return_value.order_by.return_value.first.return_value = atencion

        self.assertEqual(CitasSerializer().get_id_atencion(cita), 22)
        filter_atenciones.assert_called_once_with(
            id_paciente_patologia__id_paciente_id=14,
            id_medico_id=6,
            fecha_proxima_cita=date(2026, 11, 12),
            hora_proxima_cita=time(9, 30),
        )


class CitasViewSetTests(SimpleTestCase):
    @patch("apps.catalogos.Citas.Api.views.timezone.localdate")
    @patch("apps.catalogos.Citas.Api.views.timezone.now")
    def test_lists_future_and_unfinished_appointments_today(
        self,
        now,
        localdate,
    ):
        instante = timezone.make_aware(
            datetime(2026, 11, 12, 9, 0),
            timezone.get_current_timezone(),
        )
        now.return_value = instante
        localdate.return_value = date(2026, 11, 12)
        queryset = Mock()
        queryset.all.return_value = queryset
        queryset.filter.return_value = queryset
        view = CitasViewSet()
        view.queryset = queryset
        view.request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, rol="Administrador")
        )

        view.get_queryset()

        queryset.filter.assert_any_call(
            estado=Citas.Estado.PROGRAMADA,
        )
        queryset.filter.assert_any_call(
            Q(fecha_hora_cita__gt=instante)
            | Q(
                fecha_hora_cita__date=date(2026, 11, 12),
                atenciones__fecha_hora_fin_consulta__isnull=True,
            )
        )
        queryset.distinct.assert_called_once_with()


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
