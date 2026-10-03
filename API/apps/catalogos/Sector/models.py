from django.db import models


class Sector(models.Model):
  # Django crea automáticamente el campo ID (IdSector) como Primary Key autoincrementable

  nombre_sector = models.CharField(
      max_length=250,
      db_column="NombreSector",  # NVARCHAR(250) NOT NULL
  )

  numero_sector = models.IntegerField(
      unique=True,
      db_column="NumeroSector",  # INT NOT NULL UNIQUE
  )

  zona_procedencia = models.CharField(
      max_length=20,
      choices=[("Urbana", "Urbana"), ("Rural", "Rural")],
      db_column="ZonaProcedencia",  # Equivalente al CHECK (ZonaProcedencia IN ('Urbana','Rural'))
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
    db_table = "Sector"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Sector"
    verbose_name_plural = "Sectores"

  def __str__(self):
    return (
        f"Sector #{self.numero_sector}: {self.nombre_sector}"
        f" ({self.zona_procedencia})"
    )