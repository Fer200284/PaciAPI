from django.db import models


class TipoSalida(models.Model):
  # Django crea automáticamente el campo ID como Primary Key autoincrementable

  codigo = models.CharField(
      max_length=20,
      unique=True,
      db_column="Codigo",  # Respeta el nombre de la columna en SQL
  )

  descripcion = models.CharField(
      max_length=200,
      db_column="Descripcion",  # Respeta el nombre de la columna en SQL
  )

  estado = models.PositiveSmallIntegerField(
      default=1,
      db_column="Estado",  # 1 = activo, 0 = inactivo
  )

  class Meta:
    db_table = "TipoSalida"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Tipo de Salida"
    verbose_name_plural = "Tipos de Salida"

  def __str__(self):
    return f"{self.codigo} - {self.descripcion}"