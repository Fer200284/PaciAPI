from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from apps.catalogos.patient_scope import is_patient_user
from apps.catalogos.Pacientes.models import Pacientes
from apps.Seguridad.Usuarios.models import GerenciaInvitationCode, User


class UserSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(write_only=True, required=False)
    nombre = serializers.CharField(write_only=True, required=False)
    apellidos = serializers.CharField(write_only=True, required=False)
    cedula = serializers.CharField(write_only=True, required=False)
    fecha_de_nacimiento = serializers.DateField(write_only=True, required=False)
    celular = serializers.CharField(write_only=True, required=False)
    codigo_autorizacion = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
    )
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
            'nombre_completo',
            'nombre',
            'apellidos',
            'cedula',
            'fecha_de_nacimiento',
            'celular',
            'codigo_autorizacion',
        )
        read_only_fields = ('id', 'is_staff', 'is_active')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if request and not request.user.is_authenticated and self.instance is None:
            requested_role = attrs.get('rol', 'Paciente')
            if requested_role not in ('Paciente', 'Gerencia'):
                raise serializers.ValidationError({
                    'rol': 'El registro público solo permite crear cuentas de paciente o gerencia autorizada.'
                })
            if not attrs.get('password'):
                raise serializers.ValidationError({
                    'password': 'La contraseña es obligatoria para crear la cuenta.'
                })
            if requested_role == 'Paciente':
                attrs['rol'] = 'Paciente'
                attrs['_patient_profile'] = self._find_patient_profile(attrs)
            else:
                attrs['rol'] = 'Gerencia'
                attrs['_gerencia_invitation_id'] = self._find_gerencia_invitation(
                    attrs.get('codigo_autorizacion')
                )
                if not attrs.get('nombre_completo') and attrs.get('nombre'):
                    attrs['nombre_completo'] = attrs['nombre']
                if not attrs.get('nombre_completo') and (
                    attrs.get('first_name') or attrs.get('last_name')
                ):
                    attrs['nombre_completo'] = ' '.join(
                        part for part in (
                            attrs.get('first_name', ''),
                            attrs.get('last_name', ''),
                        ) if part
                    )
                if not attrs.get('nombre_completo'):
                    raise serializers.ValidationError({
                        'nombre_completo': 'El nombre completo es obligatorio para crear la cuenta de Gerencia.'
                    })
                if not attrs.get('first_name') and attrs.get('nombre'):
                    attrs['first_name'] = attrs['nombre']
                if not attrs.get('last_name') and attrs.get('apellidos'):
                    attrs['last_name'] = attrs['apellidos']
                if not attrs.get('first_name'):
                    attrs['first_name'] = attrs['nombre_completo']
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

    @staticmethod
    def _find_gerencia_invitation(code):
        normalized_code = (code or '').strip().upper()
        if not normalized_code:
            raise serializers.ValidationError({
                'codigo_autorizacion': 'El código de autorización es obligatorio para crear una cuenta de Gerencia.'
            })

        invitation = GerenciaInvitationCode.objects.filter(
            code=normalized_code,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()
        if invitation is None:
            raise serializers.ValidationError({
                'codigo_autorizacion': 'El código no es válido, venció o ya fue utilizado.'
            })
        return invitation.pk

    def _find_patient_profile(self, attrs):
        required_fields = (
            'cedula',
            'fecha_de_nacimiento',
            'celular',
        )
        has_full_name = bool(attrs.get('nombre_completo'))
        has_split_name = bool(attrs.get('nombre')) and bool(
            attrs.get('apellidos')
        )
        if (
            not has_full_name
            and not has_split_name
        ):
            raise serializers.ValidationError({
                'nombre_completo': (
                    'Ingresa el nombre completo tal como aparece en la ficha.'
                )
            })
        if any(not attrs.get(field) for field in required_fields):
            raise serializers.ValidationError({
                field: 'Este dato es obligatorio para verificar la ficha.'
                for field in required_fields
                if not attrs.get(field)
            })

        cedula = attrs['cedula'].replace('-', '').strip().upper()
        paciente = Pacientes.objects.filter(cedula=cedula).first()
        supplied_name = (
            attrs['nombre_completo']
            if has_full_name
            else f"{attrs['nombre']} {attrs['apellidos']}"
        )
        registered_name = (
            f"{paciente.nombre} {paciente.apellidos}"
            if paciente is not None
            else ''
        )
        if (
            paciente is None
            or paciente.usuario_id is not None
            or self._normalize_text(registered_name)
            != self._normalize_text(supplied_name)
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
        invitation_id = validated_data.pop('_gerencia_invitation_id', None)
        for field in (
            'nombre_completo',
            'nombre',
            'apellidos',
            'cedula',
            'fecha_de_nacimiento',
            'celular',
            'codigo_autorizacion',
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
            invitation = None
            if invitation_id is not None:
                invitation = GerenciaInvitationCode.objects.select_for_update().get(
                    pk=invitation_id
                )
                if not invitation.is_available:
                    raise serializers.ValidationError({
                        'codigo_autorizacion': 'El código no es válido, venció o ya fue utilizado.'
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
            if invitation is not None:
                invitation.used_at = timezone.now()
                invitation.used_by = user
                invitation.save(update_fields=('used_at', 'used_by'))
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


class GerenciaInvitationCodeSerializer(serializers.ModelSerializer):
    estado = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True,
    )
    used_by_username = serializers.CharField(
        source='used_by.username',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = GerenciaInvitationCode
        fields = (
            'id',
            'code',
            'estado',
            'created_at',
            'expires_at',
            'used_at',
            'created_by_username',
            'used_by_username',
        )
        read_only_fields = fields

    def get_estado(self, invitation):
        if invitation.used_at:
            return 'Usado'
        if invitation.expires_at <= timezone.now():
            return 'Vencido'
        return 'Disponible'