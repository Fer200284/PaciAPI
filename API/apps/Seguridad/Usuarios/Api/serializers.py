from rest_framework import serializers
from apps.catalogos.patient_scope import is_patient_user
from apps.Seguridad.Usuarios.models import User


class UserSerializer(serializers.ModelSerializer):
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

    def create(self, validated_data):
        password = validated_data.pop('password', None)

        user = User(**validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance