from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class AtencionCronico(models.Model):
  # Django crea automáticamente el campo ID (IdAtencionCronico) como PK autoincrementable

  # Llave foránea hacia la app Paciente_Patologia
  id_paciente_patologia = models.ForeignKey(
      "Paciente_Patologia.PacientePatologia",
      on_delete=models.PROTECT,
      db_column="IdPaciente_Patologia",
  )

  # Llave foránea hacia la app Medicos
  id_medico = models.ForeignKey(
      "Medicos.Medicos",
      on_delete=models.PROTECT,
      db_column="IdMedico",
  )

  fecha_atencion = models.DateField(db_column="FechaAtencion")

  # Restricción equivalente a CHECK (Peso > 0)
  peso = models.DecimalField(
      max_digits=5,
      decimal_places=2,
      blank=True,
      null=True,
      validators=[
          MinValueValidator(
              Decimal("0.01"), message="El peso debe ser mayor a 0."
          )
      ],
      db_column="Peso",
  )

  # Restricción equivalente a CHECK (Talla > 0)
  talla = models.DecimalField(
      max_digits=5,
      decimal_places=2,
      blank=True,
      null=True,
      validators=[
          MinValueValidator(
              Decimal("0.01"), message="La talla debe ser mayor a 0."
          )
      ],
      db_column="Talla",
  )

  presion_arterial = models.CharField(
      max_length=20,
      blank=True,
      null=True,
      db_column="PresionArterial",
  )

  fecha_proxima_cita = models.DateField(
      blank=True,
      null=True,
      db_column="FechaProximaCita",
  )

  asistio = models.BooleanField(
      default=True,
      db_column="Asistio",  # BIT NOT NULL DEFAULT 1
  )

  consulta_especializada = models.BooleanField(
      default=False,
      db_column="ConsultaEspecializada",  # BIT NOT NULL DEFAULT 0
  )

  observaciones = models.CharField(
      max_length=1000,
      blank=True,
      null=True,
      db_column="Observaciones",
  )

  fecha_creacion = models.DateTimeField(
      auto_now_add=True,
      db_column="FechaCreacion",
  )

  class Meta:
    db_table = "Atencion_Cronico"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Atención Crónico"
    verbose_name_plural = "Atenciones Crónicos"

  def __str__(self):
    return (
        f"Atención #{self.id} | Fecha: {self.fecha_atencion} - Médico ID:"
        f" {self.id_medico_id}"
    )