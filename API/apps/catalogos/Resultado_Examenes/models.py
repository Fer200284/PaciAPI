from django.db import models


class ResultadosExamenes(models.Model):
  # Django crea automáticamente el campo ID (IdResultadoExamen) como PK autoincrementable.

  # Llave foránea que apunta a la solicitud de examen
  id_solicitud_examen = models.ForeignKey(
      "Solicitud_Examenes.SolicitudDeExamenes",
      on_delete=models.PROTECT,
      db_column="Id_Solicitud_Examen",  # Respeta exactamente el nombre de la columna en tu SQL
  )
  valor_resultado = models.DecimalField(
      max_digits=10,
      decimal_places=2,
      blank=True,
      null=True,
      db_column="ValorResultado",  # DECIMAL(10,2) según tu script SQL
  )
  interpretacion = models.CharField(
      max_length=500,
      blank=True,
      null=True,
      db_column="Interpretacion",
  )
  fecha_resultado = models.DateTimeField(
      auto_now_add=True,
      db_column="FechaResultado",  # Equivalente a DEFAULT GETDATE()
  )

  class Meta:
    db_table = "Resultado_Examen"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Resultado de Examen"
    verbose_name_plural = "Resultados de Exámenes"

  def __str__(self):
    return (
        f"Resultado Solicitud #{self.id_solicitud_examen_id} - Valor:"
        f" {self.valor_resultado}"
    )