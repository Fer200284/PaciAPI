from django.db import models


class Medicamentos(models.Model):
  # Django crea automáticamente el campo ID (IdMedicamento) como PK autoincrementable

  # Llave foránea hacia la categoría del medicamento
  id_categoria_medicamento = models.ForeignKey(
      "Categoria_Medicamento.CategoriaMedicamento",
      on_delete=models.PROTECT,
      db_column="IdCategoriaMedicamento",
  )

  nombre_medicamento = models.CharField(
      max_length=250,
      db_column="Nombre_Medicamento",  # NVARCHAR(250) NOT NULL
  )

  presentacion = models.CharField(
      max_length=150,
      db_column="Presentacion",  # Tableta, Inyectable, Jarabe, etc.
  )

  concentracion = models.CharField(
      max_length=50,
      db_column="Concentracion",  # 500mg, 100mg/5ml, etc.
  )

  fecha_creacion = models.DateTimeField(
      auto_now_add=True, db_column="FechaCreacion"
  )

  estado = models.BooleanField(default=True, db_column="Estado")

  class Meta:
    db_table = "Medicamentos"
    verbose_name = "Medicamento"
    verbose_name_plural = "Medicamentos"
    # Restricción única compuesta equivalente a UQ_Medicamento en tu SQL
    constraints = [
        models.UniqueConstraint(
            fields=["nombre_medicamento", "concentracion"],
            name="UQ_Medicamento",
        )
    ]

  def __str__(self):
    return (
        f"{self.nombre_medicamento} {self.concentracion} ({self.presentacion})"
    )