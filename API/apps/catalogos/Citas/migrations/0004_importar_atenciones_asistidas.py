from django.db import migrations


def importar_atenciones_asistidas(apps, schema_editor):
    AtencionCronico = apps.get_model(
        "Atención_cronico",
        "AtencionCronico",
    )
    Citas = apps.get_model("Citas", "Citas")
    base = schema_editor.connection.alias

    atenciones = AtencionCronico.objects.using(base).select_related(
        "id_paciente_patologia",
    ).exclude(
        fecha_hora_llegada__isnull=True,
    )
    for atencion in atenciones.iterator():
        if atencion.id_cita_id:
            continue

        paciente_id = atencion.id_paciente_patologia.id_paciente_id
        filtros = {
            "id_paciente_id": paciente_id,
            "id_medico_id": atencion.id_medico_id,
        }
        citas_programadas = Citas.objects.using(base).filter(
            **filtros,
            fecha_hora_cita__date=atencion.fecha_atencion,
            estado="PROGRAMADA",
        )
        cita = min(
            citas_programadas,
            key=lambda item: abs(
                (item.fecha_hora_cita - atencion.fecha_hora_llegada)
                .total_seconds()
            ),
            default=None,
        )

        if cita is None:
            citas_asistidas = Citas.objects.using(base).filter(
                **filtros,
                fecha_hora_cita__date=atencion.fecha_atencion,
                estado="ASISTIO",
            )
            cita = min(
                citas_asistidas,
                key=lambda item: abs(
                    (item.fecha_atencion_real - atencion.fecha_hora_llegada)
                    .total_seconds()
                ) if item.fecha_atencion_real else float("inf"),
                default=None,
            )

        observaciones = (
            atencion.observaciones[:500]
            if atencion.observaciones
            else None
        )
        if cita is None:
            cita = Citas.objects.using(base).create(
                **filtros,
                fecha_hora_cita=atencion.fecha_hora_llegada,
                estado="ASISTIO",
                fecha_atencion_real=atencion.fecha_hora_llegada,
                observaciones=observaciones,
            )
        else:
            Citas.objects.using(base).filter(pk=cita.pk).update(
                estado="ASISTIO",
                fecha_atencion_real=atencion.fecha_hora_llegada,
                observaciones=observaciones,
            )

        AtencionCronico.objects.using(base).filter(
            pk=atencion.pk,
        ).update(id_cita_id=cita.pk)


class Migration(migrations.Migration):
    dependencies = [
        ("Citas", "0003_sincronizar_observaciones"),
        ("Atención_cronico", "0004_atencioncronico_id_cita"),
    ]

    operations = [
        migrations.RunPython(
            importar_atenciones_asistidas,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
