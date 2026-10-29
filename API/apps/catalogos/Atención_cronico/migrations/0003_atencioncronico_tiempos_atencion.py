from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Atención_cronico", "0002_atencioncronico_hora_proxima_cita"),
    ]

    operations = [
        migrations.AddField(
            model_name="atencioncronico",
            name="fecha_hora_llegada",
            field=models.DateTimeField(
                blank=True,
                db_column="FechaHoraLlegada",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="atencioncronico",
            name="fecha_hora_inicio_consulta",
            field=models.DateTimeField(
                blank=True,
                db_column="FechaHoraInicioConsulta",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="atencioncronico",
            name="fecha_hora_fin_consulta",
            field=models.DateTimeField(
                blank=True,
                db_column="FechaHoraFinConsulta",
                null=True,
            ),
        ),
    ]
