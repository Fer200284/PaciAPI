from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers


def is_patient_user(user):
    return (
        user
        and user.is_authenticated
        and getattr(user, "rol", None) == "Paciente"
    )


class PatientScopedViewSetMixin:
    patient_lookup = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if not is_patient_user(self.request.user):
            return queryset
        if not self.patient_lookup:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define patient_lookup."
            )
        return queryset.filter(**{self.patient_lookup: self.request.user})


class PatientOwnedRelationsSerializerMixin:
    patient_owned_fields = {}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        if not request or not is_patient_user(request.user):
            return attrs

        for field, patient_lookup in self.patient_owned_fields.items():
            related_object = attrs.get(field)
            if related_object is None and self.instance is not None:
                related_object = getattr(self.instance, field)
            if related_object is None:
                continue

            belongs_to_patient = related_object.__class__.objects.filter(
                pk=related_object.pk,
                **{patient_lookup: request.user},
            ).exists()
            if not belongs_to_patient:
                raise serializers.ValidationError({
                    field: "No puedes utilizar información de otro paciente."
                })
        return attrs
