# Generated by Django 5.0.4 on 2024-10-03 02:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_cg', '0004_rename_telefone_teste_telefoni'),
    ]

    operations = [
        migrations.RenameField(
            model_name='teste',
            old_name='telefoni',
            new_name='telefone',
        ),
    ]
