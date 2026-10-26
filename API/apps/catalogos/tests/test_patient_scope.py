from contextlib import nullcontext
from datetime import date
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.Seguridad.Usuarios.Api.serializers import UserSerializer
from apps.Seguridad.Usuarios.Api.views import UserViewSet
from apps.catalogos.patient_scope import (
    PatientOwnedRelationsSerializerMixin,
    PatientScopedViewSetMixin,
    is_patient_user,
)
from apps.catalogos.Pacientes.Api.serializers import PacientesSerializer


class FakeQuerySet:
    def __init__(self):
        self.filters = None

    def filter(self, **kwargs):
        self.filters = kwargs
        return self


class FakeViewSetBase:
    def get_queryset(self):
        return FakeQuerySet()


class ScopedFakeViewSet(PatientScopedViewSetMixin, FakeViewSetBase):
    patient_lookup = "owner"


class UnconfiguredFakeViewSet(PatientScopedViewSetMixin, FakeViewSetBase):
    pass


class FakeRelatedModel:
    objects = MagicMock()


class FakeOwnedRelationSerializer(
    PatientOwnedRelationsSerializerMixin,
    serializers.Serializer,
):
    relation = serializers.CharField(required=False)
    patient_owned_fields = {"relation": "owner"}


class PatientScopeTests(SimpleTestCase):
    def setUp(self):
        self.patient = SimpleNamespace(is_authenticated=True, rol="Paciente")
        self.admin = SimpleNamespace(is_authenticated=True, rol="Administrador")

    def test_detects_patient_role(self):
        self.assertTrue(is_patient_user(self.patient))
        self.assertFalse(is_patient_user(self.admin))
        self.assertFalse(is_patient_user(SimpleNamespace(is_authenticated=False)))

    def test_patient_queryset_is_scoped_to_authenticated_user(self):
        view = ScopedFakeViewSet()
        view.request = SimpleNamespace(user=self.patient)

        queryset = view.get_queryset()

        self.assertEqual(queryset.filters, {"owner": self.patient})

    def test_non_patient_queryset_remains_unfiltered(self):
        view = ScopedFakeViewSet()
        view.request = SimpleNamespace(user=self.admin)

        queryset = view.get_queryset()

        self.assertIsNone(queryset.filters)

    def test_patient_view_without_scope_fails_closed(self):
        view = UnconfiguredFakeViewSet()
        view.request = SimpleNamespace(user=self.patient)

        with self.assertRaises(ImproperlyConfigured):
            view.get_queryset()

    def test_related_records_must_belong_to_patient(self):
        relation = FakeRelatedModel()
        relation.pk = 42
        request = SimpleNamespace(user=self.patient)
        serializer = FakeOwnedRelationSerializer(context={"request": request})
        FakeRelatedModel.objects.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError):
            serializer.validate({"relation": relation})

        FakeRelatedModel.objects.filter.assert_called_with(
            pk=42,
            owner=self.patient,
        )

    def test_patient_cannot_escalate_role(self):
        serializer = UserSerializer(
            instance=SimpleNamespace(rol="Paciente"),
            context={"request": SimpleNamespace(user=self.patient)},
        )

        with self.assertRaises(ValidationError):
            serializer.validate({"rol": "Administrador"})

    def test_public_registration_cannot_create_privileged_role(self):
        serializer = UserSerializer(
            context={
                "request": SimpleNamespace(
                    user=SimpleNamespace(is_authenticated=False)
                )
            },
        )

        with self.assertRaises(ValidationError):
            serializer.validate({"rol": "Administrador"})

    @patch("apps.Seguridad.Usuarios.Api.serializers.Pacientes.objects")
    def test_public_registration_requires_matching_patient_data(self, patients):
        profile = SimpleNamespace(
            usuario_id=None,
            nombre="Juan Carlos",
            apellidos="Pérez López",
            fecha_de_nacimiento=date(1990, 1, 1),
            celular="88888888",
        )
        patients.filter.return_value.first.return_value = profile
        serializer = UserSerializer(
            context={
                "request": SimpleNamespace(
                    user=SimpleNamespace(is_authenticated=False)
                )
            }
        )

        attrs = serializer.validate({
            "username": "juan",
            "password": "secure-password",
            "nombre": " juan   carlos ",
            "apellidos": "PÉREZ LÓPEZ",
            "cedula": "0010101000000-a",
            "fecha_de_nacimiento": date(1990, 1, 1),
            "celular": "88888888",
        })

        self.assertIs(attrs["_patient_profile"], profile)
        self.assertEqual(attrs["rol"], "Paciente")
        patients.filter.assert_called_once_with(cedula="0010101000000A")

    @patch("apps.Seguridad.Usuarios.Api.serializers.Pacientes.objects")
    def test_public_registration_accepts_single_full_name_field(self, patients):
        profile = SimpleNamespace(
            usuario_id=None,
            nombre="Dariana De Jesus",
            apellidos="Vivas Ampies",
            fecha_de_nacimiento=date(1990, 1, 1),
            celular="88888888",
        )
        patients.filter.return_value.first.return_value = profile
        serializer = UserSerializer(
            context={
                "request": SimpleNamespace(
                    user=SimpleNamespace(is_authenticated=False)
                )
            }
        )

        attrs = serializer.validate({
            "username": "dariana",
            "password": "secure-password",
            "nombre_completo": "Dariana De Jesus Vivas Ampies",
            "cedula": "0010101000000A",
            "fecha_de_nacimiento": date(1990, 1, 1),
            "celular": "88888888",
        })

        self.assertIs(attrs["_patient_profile"], profile)

    @patch("apps.Seguridad.Usuarios.Api.serializers.Pacientes.objects")
    def test_public_registration_rejects_nonmatching_full_name(self, patients):
        profile = SimpleNamespace(
            usuario_id=None,
            nombre="Dariana De Jesus",
            apellidos="Vivas Ampies",
            fecha_de_nacimiento=date(1990, 1, 1),
            celular="88888888",
        )
        patients.filter.return_value.first.return_value = profile
        serializer = UserSerializer(
            context={
                "request": SimpleNamespace(
                    user=SimpleNamespace(is_authenticated=False)
                )
            }
        )

        with self.assertRaises(ValidationError):
            serializer.validate({
                "username": "dariana",
                "password": "secure-password",
                "nombre_completo": "Dariana Vivas",
                "cedula": "0010101000000A",
                "fecha_de_nacimiento": date(1990, 1, 1),
                "celular": "88888888",
            })

    def test_public_registration_rejects_missing_patient_identity(self):
        serializer = UserSerializer(
            context={
                "request": SimpleNamespace(
                    user=SimpleNamespace(is_authenticated=False)
                )
            }
        )

        with self.assertRaises(ValidationError):
            serializer.validate({
                "username": "juan",
                "password": "secure-password",
            })

    def test_patient_profile_rejects_linking_non_patient_account(self):
        serializer = PacientesSerializer()

        with self.assertRaises(ValidationError):
            serializer.validate_usuario(SimpleNamespace(rol="Administrador"))

    def test_patient_relation_paths_resolve_in_model_metadata(self):
        paths = (
            (
                "Pacientes",
                "Pacientes",
                "PacientesViewSet",
            ),
            (
                "Paciente_Patologia",
                "PacientePatologia",
                "PacientePatologiaViewSet",
            ),
            (
                "Atención_cronico",
                "AtencionCronico",
                "AtencionCronicoViewSet",
            ),
            (
                "Solicitud_Examenes",
                "SolicitudDeExamenes",
                "SolicitudDeExamenesViewSet",
            ),
            (
                "Resultado_Examenes",
                "ResultadosExamenes",
                "ResultadosExamenesViewSet",
            ),
            (
                "Tratamiento",
                "Tratamiento",
                "TratamientoViewSet",
            ),
            (
                "Detalle_Tratamiento",
                "DetalleTratamiento",
                "DetalleTratamientoViewSet",
            ),
        )

        for app, model_name, view_name in paths:
            with self.subTest(model=model_name):
                model = getattr(
                    import_module(f"apps.catalogos.{app}.models"),
                    model_name,
                )
                viewset = getattr(
                    import_module(f"apps.catalogos.{app}.Api.views"),
                    view_name,
                )
                lookup = viewset.patient_lookup
                current_model = model
                field_names = lookup.split("__")
                for index, field_name in enumerate(field_names):
                    field = current_model._meta.get_field(field_name)
                    if index < len(field_names) - 1:
                        current_model = field.related_model

                serializer_module = import_module(
                    f"apps.catalogos.{app}.Api.serializers"
                )
                serializer = getattr(
                    serializer_module,
                    viewset.serializer_class.__name__,
                )
                for field_name, relation_lookup in getattr(
                    serializer,
                    "patient_owned_fields",
                    {},
                ).items():
                    current_model = model._meta.get_field(field_name).related_model
                    for index, relation_field in enumerate(relation_lookup.split("__")):
                        field = current_model._meta.get_field(relation_field)
                        if index < len(relation_lookup.split("__")) - 1:
                            current_model = field.related_model


class MobileSummaryTests(SimpleTestCase):
    def test_patient_summary_returns_only_next_appointment_and_live_records(self):
        patient = SimpleNamespace(
            is_authenticated=True,
            rol="Paciente",
            pk=17,
        )
        appointment = {
            "id": 23,
            "fecha_proxima_cita": date(2026, 12, 1),
            "hora_proxima_cita": None,
            "id_medico__nombre": "Ana",
            "id_medico__apellidos": "Lopez",
            "id_paciente_patologia__id_patologia_cronica__nombre_patologia": "Asma",
        }
        medication = {
            "id": 31,
            "id_medicamento": 61,
            "id_medicamento__nombre_medicamento": "Medicamento actualizado",
            "id_medicamento__presentacion": "Tableta",
            "id_medicamento__concentracion": "500 mg",
            "id_medicamento__estado": True,
            "cantidad_entregada": 30,
            "indicacion": "Una diaria",
            "id_tratamiento__fecha_tratamiento": date(2026, 10, 1),
            "id_tratamiento__observaciones": None,
        }
        exam_request = {
            "id": 41,
            "id_examen_de_laboratorio": 71,
            "id_examen_de_laboratorio__nombre_examen": "Hemograma",
            "id_examen_de_laboratorio__unidad_medida": "g/dL",
            "id_examen_de_laboratorio__valor_referencia": "12-16",
            "id_examen_de_laboratorio__estado": True,
            "indicaciones": "En ayunas",
            "fecha_de_envio": None,
        }
        exam_result = {
            "id": 51,
            "id_solicitud_examen": 41,
            "valor_resultado": 12,
            "interpretacion": "Normal",
            "fecha_resultado": None,
        }
        with (
            patch(
                "apps.Seguridad.Usuarios.Api.views.Pacientes.objects"
            ) as patients,
            patch(
                "apps.Seguridad.Usuarios.Api.views.AtencionCronico.objects"
            ) as appointments,
            patch(
                "apps.Seguridad.Usuarios.Api.views.DetalleTratamiento.objects"
            ) as medication_details,
            patch(
                "apps.Seguridad.Usuarios.Api.views.SolicitudDeExamenes.objects"
            ) as exam_requests,
            patch(
                "apps.Seguridad.Usuarios.Api.views.ResultadosExamenes.objects"
            ) as exam_results,
        ):
            patients.filter.return_value.exists.return_value = True
            appointments.filter.return_value.order_by.return_value.values.return_value.first.return_value = appointment
            medication_details.filter.return_value.order_by.return_value.values.return_value = [
                medication
            ]
            exam_requests.filter.return_value.order_by.return_value.values.return_value = [
                exam_request
            ]
            exam_results.filter.return_value.order_by.return_value.values.return_value = [
                exam_result
            ]

            request = APIRequestFactory().get("/api/usuarios/resumen-movil/")
            force_authenticate(request, user=patient)
            response = UserViewSet.as_view({
                "get": "resumen_movil",
            })(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["proxima_cita"]["fecha"], date(2026, 12, 1))
        self.assertEqual(
            response.data["medicamentos"][0]["nombre"],
            "Medicamento actualizado",
        )
        self.assertEqual(
            response.data["examenes_solicitados"][0]["resultados"][0]["interpretacion"],
            "Normal",
        )
        appointment_filters = appointments.filter.call_args.kwargs
        self.assertEqual(
            appointment_filters["id_paciente_patologia__id_paciente__usuario"],
            patient,
        )
        self.assertEqual(
            appointment_filters["fecha_proxima_cita__gte"],
            timezone.localdate(),
        )
        self.assertEqual(
            medication_details.filter.call_args.kwargs[
                "id_tratamiento__id_atencion_cronico__id_paciente_patologia__id_paciente__usuario"
            ],
            patient,
        )
        self.assertEqual(
            exam_requests.filter.call_args.kwargs[
                "id_atencion_cronico__id_paciente_patologia__id_paciente__usuario"
            ],
            patient,
        )
        exam_results.filter.assert_called_once_with(
            id_solicitud_examen__in=[41]
        )

    def test_non_patient_cannot_access_mobile_summary(self):
        manager = SimpleNamespace(
            is_authenticated=True,
            rol="Administrador",
            pk=1,
        )
        request = APIRequestFactory().get("/api/usuarios/resumen-movil/")
        force_authenticate(request, user=manager)

        response = UserViewSet.as_view({
            "get": "resumen_movil",
        })(request)

        self.assertEqual(response.status_code, 403)


class GerenciaAccountRegistrationTests(SimpleTestCase):
    @patch("apps.Seguridad.Usuarios.Api.serializers.transaction.atomic")
    @patch("apps.Seguridad.Usuarios.Api.serializers.User")
    def test_public_gerencia_registration_creates_account_without_invitation(
        self,
        user_model,
        atomic,
    ):
        atomic.return_value = nullcontext()
        serializer = UserSerializer(
            context={
                "request": SimpleNamespace(
                    user=SimpleNamespace(is_authenticated=False)
                )
            }
        )

        attrs = serializer.validate({
            "username": "gerencia",
            "password": "secure-password",
            "rol": "Gerencia",
            "nombre_completo": "Carlos Mendoza",
        })

        created_user = serializer.create(attrs)

        self.assertIs(created_user, user_model.return_value)
        user_model.assert_called_once_with(
            username="gerencia",
            rol="Gerencia",
            first_name="Carlos Mendoza",
        )
        created_user.set_password.assert_called_once_with("secure-password")
        self.assertNotIn("codigo_autorizacion", serializer.fields)
