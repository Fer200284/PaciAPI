from django.contrib.auth.models import AbstractUser
from django.db import models


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