from django.core.validators import MinValueValidator
from django.db import models


class DetalleTratamiento(models.Model):
  # Django crea automáticamente el campo ID (IdDetalleTratamiento) como Primary Key autoincrementable

  # Llave foránea que apunta a la tabla Tratamiento
  id_tratamiento = models.ForeignKey(
      "Tratamiento.Tratamiento",
      on_delete=models.PROTECT,
      db_column="IdTratamiento",  # Respeta el nombre de la columna en SQL
  )

  # Llave foránea que apunta al catálogo Medicamentos
  id_medicamento = models.ForeignKey(
      "Medicamentos.Medicamentos",
      on_delete=models.PROTECT,
      db_column="IdMedicamento",  # Respeta el nombre de la columna en SQL
  )

  # Equivalente a INT NOT NULL con restricción CHECK (CantidadEntregada > 0)
  cantidad_entregada = models.IntegerField(
      validators=[
          MinValueValidator(1, message="La cantidad entregada debe ser mayor a 0.")
      ],
      db_column="CantidadEntregada",
  )

  indicacion = models.CharField(
      max_length=500,
      db_column="Indicacion",  # NVARCHAR(500) NOT NULL
  )

  class Meta:
    db_table = "Detalle_Tratamiento"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Detalle de Tratamiento"
    verbose_name_plural = "Detalles de Tratamientos"

  def __str__(self):
    return (
        f"Detalle #{self.id} | Tratamiento #{self.id_tratamiento_id} - Cantidad:"
        f" {self.cantidad_entregada}"
    )