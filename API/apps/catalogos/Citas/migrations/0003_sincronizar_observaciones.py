from datetime import datetime

from django.db import migrations
from django.utils import timezone


def sincronizar_observaciones_atencion(apps, schema_editor):
    AtencionCronico = apps.get_model(
        "Atención_cronico",
        "AtencionCronico",
    )
    Citas = apps.get_model("Citas", "Citas")
    base = schema_editor.connection.alias

    atenciones = AtencionCronico.objects.using(base).select_related(
        "id_paciente_patologia",
    ).exclude(
        fecha_proxima_cita__isnull=True,
    ).exclude(
        hora_proxima_cita__isnull=True,
    )
    for atencion in atenciones.iterator():
        fecha_hora = timezone.make_aware(
            datetime.combine(
                atencion.fecha_proxima_cita,
                atencion.hora_proxima_cita,
            ),
            timezone.get_current_timezone(),
        )
        cita = Citas.objects.using(base).filter(
            id_paciente_id=atencion.id_paciente_patologia.id_paciente_id,
            id_medico_id=atencion.id_medico_id,
            fecha_hora_cita=fecha_hora,
        ).order_by("pk").first()
        if cita:
            observaciones = (
                atencion.observaciones[:500]
                if atencion.observaciones
                else None
            )
            Citas.objects.using(base).filter(pk=cita.pk).update(
                observaciones=observaciones,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("Citas", "0002_importar_proximas_citas"),
    ]

    operations = [
        migrations.RunPython(
            sincronizar_observaciones_atencion,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
