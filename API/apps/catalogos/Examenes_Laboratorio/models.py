from django.db import models


class ExamenesDeLaboratorio(models.Model):
  # Django crea automáticamente el campo ID (IdExamen_de_Laboratorio) como PK autoincrementable.

  nombre_examen = models.CharField(
      max_length=250,
      unique=True,
      db_column="Nombre_examen",  # Respeta el nombre exacto de la columna SQL
  )
  unidad_medida = models.CharField(
      max_length=50,
      blank=True,
      null=True,
      db_column="UnidadMedida",
  )
  valor_referencia = models.CharField(
      max_length=100,
      blank=True,
      null=True,
      db_column="ValorReferencia",
  )
  fecha_creacion = models.DateTimeField(
      auto_now_add=True,
      db_column="FechaCreacion",  # Equivalente a DEFAULT GETDATE()
  )
  estado = models.BooleanField(
      default=True,
      db_column="Estado",  # Equivalente a BIT NOT NULL DEFAULT 1
  )

  class Meta:
    db_table = "Examenes_Laboratorio"  # Nombre exacto de la tabla en SQL
    verbose_name = "Examen de Laboratorio"
    verbose_name_plural = "Exámenes de Laboratorio"

  def __str__(self):
    return (
        f"{self.nombre_examen} ({self.unidad_medida})"
        if self.unidad_medida
        else self.nombre_examen
    )