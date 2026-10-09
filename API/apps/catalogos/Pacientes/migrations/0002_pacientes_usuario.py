import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Pacientes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='pacientes',
            name='usuario',
            field=models.OneToOneField(
                blank=True,
                db_column='UsuarioId',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='paciente',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
