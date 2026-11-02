from django.db import models


class EstadoCita(models.TextChoices):
    PROGRAMADA = "PROGRAMADA", "Programada"
    ASISTIO = "ASISTIO", "Asistió"
    NO_ASISTIO = "NO_ASISTIO", "No asistió"
    CANCELADA = "CANCELADA", "Cancelada"
    REPROGRAMADA = "REPROGRAMADA", "Reprogramada"


class Citas(models.Model):
    Estado = EstadoCita
    id = models.BigAutoField(
        primary_key=True,
        db_column="Id",
    )
    id_paciente = models.ForeignKey(
        "Pacientes.Pacientes",
        on_delete=models.PROTECT,
        db_column="IdPaciente",
        related_name="citas",
        db_index=False,
    )
    id_medico = models.ForeignKey(
        "Medicos.Medicos",
        on_delete=models.PROTECT,
        db_column="IdMedico",
        related_name="citas",
        db_index=False,
    )
    fecha_hora_cita = models.DateTimeField(db_column="FechaHoraCita")
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        db_column="Estado",
    )
    fecha_atencion_real = models.DateTimeField(
        blank=True,
        null=True,
        db_column="FechaAtencionReal",
    )
    observaciones = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        db_column="Observaciones",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column="FechaCreacion",
    )

    class Meta:
        db_table = "Citas"
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        constraints = [
            models.CheckConstraint(
                check=models.Q(estado__in=EstadoCita.values),
                name="CK_Citas_Estado",
            ),
        ]
        indexes = [
            models.Index(fields=["id_paciente"], name="IX_Citas_Paciente"),
            models.Index(fields=["id_medico"], name="IX_Citas_Medico"),
            models.Index(
                fields=["fecha_hora_cita"],
                name="IX_Citas_FechaHoraCita",
            ),
        ]

    def __str__(self):
        return f"Cita #{self.pk} - {self.fecha_hora_cita}"
