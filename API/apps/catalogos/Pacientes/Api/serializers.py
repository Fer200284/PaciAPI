from rest_framework import serializers
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