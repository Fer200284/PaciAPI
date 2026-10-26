from importlib import import_module
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.Seguridad.Usuarios.Api.serializers import UserSerializer
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

        self.assertEqual(serializer.validate({})["rol"], "Paciente")

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

        self.assertEqual(serializer.validate({})["rol"], "Paciente")

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
