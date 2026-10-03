from django.db import models


class PacientePatologia(models.Model):
  # Llave foránea hacia la app Pacientes
  id_paciente = models.ForeignKey(
      "Pacientes.Pacientes",
      on_delete=models.PROTECT,
      db_column="Idpaciente",  # Respeta exactamente el nombre de la columna en SQL
  )

  # Llave foránea hacia la app Patologias_Cronicas
  id_patologia_cronica = models.ForeignKey(
      "Patologias_Cronicas.PatologiasCronicas",
      on_delete=models.PROTECT,
      db_column="IDPatologiaCRonica",  # Respeta exactamente el nombre de la columna en SQL
  )

  fecha_de_diagnostico = models.DateField(db_column="fecha_de_Diagnostico")

  estado = models.BooleanField(
      default=True,
      db_column="Estado",  # Equivalente a BIT NOT NULL DEFAULT 1
  )

  observaciones = models.CharField(
      max_length=500,
      blank=True,
      null=True,
      db_column="Observaciones",
  )

  class Meta:
    db_table = "Paciente_Patologia"  # Nombre exacto de la tabla en SQL
    verbose_name = "Paciente Patología"
    verbose_name_plural = "Pacientes Patologías"
    # Restricción única compuesta equivalente a UNIQUE (IDPatologiaCRonica, Idpaciente) en SQL
    constraints = [
        models.UniqueConstraint(
            fields=["id_patologia_cronica", "id_paciente"],
            name="UQ_Paciente_Patologia",
        )
    ]

  def __str__(self):
    return (
        f"Paciente #{self.id_paciente_id} - Patología ID:"
        f" {self.id_patologia_cronica_id}"
    )