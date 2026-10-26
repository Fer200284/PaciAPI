from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):

    class Roles(models.TextChoices):
        PACIENTE = 'Paciente', 'Paciente'
        GERENCIA = 'Gerencia', 'Gerencia'
        ADMINISTRADOR = 'Administrador', 'Administrador'

    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PACIENTE
    )


class GerenciaInvitationCode(models.Model):
    code = models.CharField(max_length=16, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gerencia_invitation_codes_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='gerencia_invitation_codes_used',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Código de invitación de gerencia'
        verbose_name_plural = 'Códigos de invitación de gerencia'

    @property
    def is_available(self):
        return (
            self.used_at is None
            and self.expires_at > timezone.now()
        )

    def __str__(self):
        return self.code