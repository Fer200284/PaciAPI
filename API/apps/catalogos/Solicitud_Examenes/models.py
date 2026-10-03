from django.db import models


class SolicitudDeExamenes(models.Model):
  # Django crea automáticamente el ID autoincrementable (Id_Solicitud_Examen)

  # Llave foránea al catálogo de exámenes de laboratorio
  id_examen_de_laboratorio = models.ForeignKey(
      "Examenes_Laboratorio.ExamenesDeLaboratorio",
      on_delete=models.PROTECT,
      db_column="IdExamen_de_Laboratorio",
  )

  # Llave foránea a la atención del paciente crónico
  id_atencion_cronico = models.ForeignKey(
      "Atención_cronico.AtencionCronico",
      on_delete=models.PROTECT,
      db_column="IdAtencionCronico",
  )

  indicaciones = models.CharField(
      max_length=450,
      db_column="Indicaciones",  # Nvarchar(450) NOT NULL en tu SQL
  )

  fecha_de_envio = models.DateTimeField(
      auto_now_add=True,
      db_column="fecha_de_envio",  # Equivalente a DEFAULT GETDATE()
  )

  class Meta:
    db_table = "Solicitud_examenes"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Solicitud de Examen"
    verbose_name_plural = "Solicitudes de Exámenes"

  def __str__(self):
    return (
        f"Solicitud #{self.id} - Examen ID: {self.id_examen_de_laboratorio_id}"
    )