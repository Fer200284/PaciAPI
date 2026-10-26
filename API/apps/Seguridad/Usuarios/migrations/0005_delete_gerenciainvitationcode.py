from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Usuarios', '0004_gerenciainvitationcode'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GerenciaInvitationCode',
        ),
    ]
