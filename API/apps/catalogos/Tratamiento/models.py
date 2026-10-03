from django.db import models


class Tratamiento(models.Model):
  # Django crea automáticamente el ID autoincrementable (IdTratamiento) como Primary Key

  # Llave foránea que apunta a la atención del paciente crónico
  id_atencion_cronico = models.ForeignKey(
      "Atención_cronico.AtencionCronico",
      on_delete=models.PROTECT,
      db_column="IdAtencionCronico",  # Respeta exactamente el nombre de la columna en SQL
  )

  fecha_tratamiento = models.DateField(
      auto_now_add=True,  # Equivalente a DEFAULT GETDATE() o fecha actual por defecto
      db_column="FechaTratamiento",
  )

  observaciones = models.CharField(
      max_length=500,
      blank=True,
      null=True,
      db_column="Observaciones",
  )

  class Meta:
    db_table = "Tratamiento"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Tratamiento"
    verbose_name_plural = "Tratamientos"

  def __str__(self):
    return f"Tratamiento #{self.id} - Atención #{self.id_atencion_cronico_id}"