# Generated by Django 5.0.4 on 2024-09-24 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Empresas',
            fields=[
                ('id_empresa', models.AutoField(primary_key=True, serialize=False)),
                ('empresa', models.TextField(max_length=255)),
                ('cnpj', models.TextField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Teste',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.TextField()),
                ('telefone', models.TextField()),
            ],
        ),
    ]
