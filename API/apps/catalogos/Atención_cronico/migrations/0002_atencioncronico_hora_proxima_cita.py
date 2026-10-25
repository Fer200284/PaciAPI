from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Atención_cronico', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='atencioncronico',
            name='hora_proxima_cita',
            field=models.TimeField(
                blank=True,
                db_column='HoraProximaCita',
                null=True,
            ),
        ),
    ]
