from django.core.validators import RegexValidator
from django.db import models


class Pacientes(models.Model):
  # Validador para el celular: exactamente 8 dígitos numéricos
  validador_celular = RegexValidator(
      regex=r"^\d{8}$", message="El celular debe contener exactamente 8 dígitos."
  )

  # Validador para la cédula nicaragüense: 13 números seguidos de una letra mayúscula
  validador_cedula = RegexValidator(
      regex=r"^\d{13}[A-Z]$",
      message=(
          "La cédula debe tener 13 dígitos numéricos seguidos de una letra"
          " mayúscula (Ej. 0010101000000A)."
      ),
  )

  # Llave foránea hacia el catálogo Sector (opcional u obligatoria según tu SQL)
  id_sector = models.ForeignKey(
      "Sector.Sector",
      on_delete=models.PROTECT,
      db_column="IdSector",
      blank=True,
      null=True,
  )

  nombre = models.CharField(max_length=150, db_column="Nombre")
  apellidos = models.CharField(max_length=150, db_column="Apellidos")

  sexo = models.CharField(
      max_length=1,
      choices=[("M", "Masculino"), ("F", "Femenino")],
      db_column="sexo",  # Equivalente al CHECK de sexo IN ('M', 'F')
  )

  fecha_de_nacimiento = models.DateField(
      db_column="Fecha_de_Nacimiento"  # Validación de fecha menor o igual a hoy se maneja mejor en formularios/clean
  )

  celular = models.CharField(
      max_length=8,
      validators=[validador_celular],
      db_column="celular",
  )

  cedula = models.CharField(
      max_length=14,
      unique=True,
      validators=[validador_cedula],
      db_column="Cedula",
  )

  direccion = models.CharField(max_length=400, db_column="Direccion")
  barrio = models.CharField(max_length=150, db_column="Barrio")

  fecha_creacion = models.DateTimeField(
      auto_now_add=True, db_column="FechaCreacion"
  )

  estado = models.BooleanField(default=True, db_column="Estado")

  class Meta:
    db_table = "Pacientes"
    verbose_name = "Paciente"
    verbose_name_plural = "Pacientes"

  def __str__(self):
    return f"{self.nombre} {self.apellidos} - Cédula: {self.cedula}"