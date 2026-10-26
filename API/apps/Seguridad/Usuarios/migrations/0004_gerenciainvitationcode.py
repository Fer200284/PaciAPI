import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Usuarios', '0003_alter_user_rol'),
    ]

    operations = [
        migrations.CreateModel(
            name='GerenciaInvitationCode',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('code', models.CharField(max_length=16, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='gerencia_invitation_codes_created',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'used_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='gerencia_invitation_codes_used',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Código de invitación de gerencia',
                'verbose_name_plural': 'Códigos de invitación de gerencia',
                'ordering': ('-created_at',),
            },
        ),
    ]
