from datetime import datetime

from django.db import migrations
from django.utils import timezone


def importar_proximas_citas(apps, schema_editor):
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
        filtros = {
            "id_paciente_id": atencion.id_paciente_patologia.id_paciente_id,
            "id_medico_id": atencion.id_medico_id,
            "fecha_hora_cita": fecha_hora,
            "estado": "PROGRAMADA",
        }
        if not Citas.objects.using(base).filter(**filtros).exists():
            Citas.objects.using(base).create(**filtros)


class Migration(migrations.Migration):
    dependencies = [
        ("Citas", "0001_initial"),
        ("Atención_cronico", "0004_atencioncronico_id_cita"),
    ]

    operations = [
        migrations.RunPython(
            importar_proximas_citas,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
