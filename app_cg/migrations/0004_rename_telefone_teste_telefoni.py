# Generated by Django 5.0.4 on 2024-10-03 02:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_cg', '0003_contrato_codusuario_empresas_razaosocial_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='teste',
            old_name='telefone',
            new_name='telefoni',
        ),
    ]
