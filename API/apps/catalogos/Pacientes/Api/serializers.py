from rest_framework import serializers
from apps.catalogos.patient_scope import is_patient_user
from ..models import Pacientes


class PacientesSerializer(serializers.ModelSerializer):
    cedula = serializers.CharField(
        max_length=14,
        validators=[Pacientes.validador_cedula],
    )

    class Meta:
        model = Pacientes
        fields = '__all__'  # Esto incluye todos los campos de tu modelo automáticamente

    def validate_cedula(self, value):
        pacientes_con_cedula = Pacientes.objects.filter(cedula=value)
        if self.instance:
            pacientes_con_cedula = pacientes_con_cedula.exclude(pk=self.instance.pk)
        if pacientes_con_cedula.exists():
            raise serializers.ValidationError(
                "No se puede guardar el paciente porque esta cédula ya pertenece a otro paciente."
            )
        return value

    def validate_usuario(self, value):
        if value is None:
            return value
        if value.rol != "Paciente":
            raise serializers.ValidationError(
                "Solo se pueden vincular cuentas con rol Paciente."
            )

        pacientes_con_usuario = Pacientes.objects.filter(usuario=value)
        if self.instance:
            pacientes_con_usuario = pacientes_con_usuario.exclude(
                pk=self.instance.pk
            )
        if pacientes_con_usuario.exists():
            raise serializers.ValidationError(
                "Esta cuenta ya está vinculada a otra ficha de paciente."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        if request and is_patient_user(request.user):
            attrs["usuario"] = request.user
        return attrs