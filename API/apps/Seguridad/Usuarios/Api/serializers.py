from django.db import transaction
from rest_framework import serializers
from apps.catalogos.patient_scope import is_patient_user
from apps.catalogos.Pacientes.models import Pacientes
from apps.Seguridad.Usuarios.models import User


class UserSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(write_only=True, required=False)
    apellidos = serializers.CharField(write_only=True, required=False)
    cedula = serializers.CharField(write_only=True, required=False)
    fecha_de_nacimiento = serializers.DateField(write_only=True, required=False)
    celular = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'rol',
            'is_staff',
            'is_active',
            'nombre',
            'apellidos',
            'cedula',
            'fecha_de_nacimiento',
            'celular',
        )
        read_only_fields = ('id', 'is_staff', 'is_active')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if request and not request.user.is_authenticated and self.instance is None:
            requested_role = attrs.get('rol', 'Paciente')
            if requested_role != 'Paciente':
                raise serializers.ValidationError({
                    'rol': 'El registro público solo permite crear cuentas de paciente.'
                })
            attrs['rol'] = 'Paciente'
            if not attrs.get('password'):
                raise serializers.ValidationError({
                    'password': 'La contraseña es obligatoria para crear la cuenta.'
                })
            attrs['_patient_profile'] = self._find_patient_profile(attrs)
        elif request and is_patient_user(request.user):
            requested_role = attrs.get(
                'rol',
                getattr(self.instance, 'rol', 'Paciente'),
            )
            if requested_role != 'Paciente':
                raise serializers.ValidationError({
                    'rol': 'No puedes cambiar tu rol de paciente.'
                })
            attrs['rol'] = 'Paciente'
        return attrs

    def _find_patient_profile(self, attrs):
        required_fields = (
            'nombre',
            'apellidos',
            'cedula',
            'fecha_de_nacimiento',
            'celular',
        )
        if any(not attrs.get(field) for field in required_fields):
            raise serializers.ValidationError({
                field: 'Este dato es obligatorio para verificar la ficha.'
                for field in required_fields
                if not attrs.get(field)
            })

        cedula = attrs['cedula'].replace('-', '').strip().upper()
        paciente = Pacientes.objects.filter(cedula=cedula).first()
        if (
            paciente is None
            or paciente.usuario_id is not None
            or self._normalize_text(paciente.nombre)
            != self._normalize_text(attrs['nombre'])
            or self._normalize_text(paciente.apellidos)
            != self._normalize_text(attrs['apellidos'])
            or paciente.fecha_de_nacimiento != attrs['fecha_de_nacimiento']
            or ''.join(filter(str.isdigit, paciente.celular))
            != ''.join(filter(str.isdigit, attrs['celular']))
        ):
            raise serializers.ValidationError({
                'non_field_errors': [
                    'No se pudo verificar la ficha. Revisa los datos o contacta a la clínica.'
                ]
            })
        return paciente

    @staticmethod
    def _normalize_text(value):
        return ' '.join(value.split()).casefold()

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        patient_profile = validated_data.pop('_patient_profile', None)
        for field in (
            'nombre',
            'apellidos',
            'cedula',
            'fecha_de_nacimiento',
            'celular',
        ):
            validated_data.pop(field, None)

        with transaction.atomic():
            if patient_profile is not None:
                patient_profile = Pacientes.objects.select_for_update().get(
                    pk=patient_profile.pk
                )
                if patient_profile.usuario_id is not None:
                    raise serializers.ValidationError({
                        'non_field_errors': [
                            'No se pudo verificar la ficha. Revisa los datos o contacta a la clínica.'
                        ]
                    })

            user = User(**validated_data)
            if patient_profile is not None:
                user.first_name = user.first_name or patient_profile.nombre
                user.last_name = user.last_name or patient_profile.apellidos
            if password:
                user.set_password(password)
            user.save()
            if patient_profile is not None:
                patient_profile.usuario = user
                patient_profile.save(update_fields=('usuario',))
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class MobileAppointmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora = serializers.TimeField(allow_null=True)
    medico = serializers.DictField()
    patologia = serializers.CharField()


class MobileMedicationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    medicamento_id = serializers.IntegerField()
    nombre = serializers.CharField()
    presentacion = serializers.CharField()
    concentracion = serializers.CharField()
    activo = serializers.BooleanField()
    cantidad_entregada = serializers.IntegerField()
    indicacion = serializers.CharField()
    fecha_tratamiento = serializers.DateField()
    observaciones = serializers.CharField(allow_null=True)


class MobileExamResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    valor_resultado = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
    )
    interpretacion = serializers.CharField(allow_null=True)
    fecha_resultado = serializers.DateTimeField()


class MobileExamRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    examen_id = serializers.IntegerField()
    nombre = serializers.CharField()
    unidad_medida = serializers.CharField(allow_null=True)
    valor_referencia = serializers.CharField(allow_null=True)
    activo = serializers.BooleanField()
    indicaciones = serializers.CharField()
    fecha_solicitud = serializers.DateTimeField()
    resultados = MobileExamResultSerializer(many=True)


class MobileSummarySerializer(serializers.Serializer):
    proxima_cita = MobileAppointmentSerializer(allow_null=True)
    medicamentos = MobileMedicationSerializer(many=True)
    examenes_solicitados = MobileExamRequestSerializer(many=True)