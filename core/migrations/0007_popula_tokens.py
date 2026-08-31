import secrets
from django.db import migrations


def gerar_tokens(apps, schema_editor):
    Bolsista = apps.get_model('core', 'Bolsista')
    for bolsista in Bolsista.objects.all():
        bolsista.token = secrets.token_urlsafe(24)
        bolsista.save(update_fields=['token'])


def reverter(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_bolsista_token'),
    ]

    operations = [
        migrations.RunPython(gerar_tokens, reverter),
    ]