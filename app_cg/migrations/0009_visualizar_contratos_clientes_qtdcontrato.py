# Generated by Django 5.0.4 on 2024-10-10 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cg', '0008_itensadicionais_dtatualiz'),
    ]

    operations = [
        migrations.CreateModel(
            name='Visualizar_contratos',
            fields=[
                ('codvcontrato', models.AutoField(primary_key=True, serialize=False)),
                ('codcontrato', models.IntegerField()),
                ('codcliente', models.IntegerField()),
                ('nome', models.TextField(default='Cliente', max_length=100)),
                ('dtevento', models.TextField(max_length=10, null=True)),
                ('enderecoevento', models.TextField(max_length=100, null=True)),
                ('tipoevento', models.TextField(max_length=20, null=True)),
                ('tipocontrato', models.TextField(default='X', max_length=1)),
            ],
            options={
                'db_table': 'v_visualizar_contratos',
                'managed': False,
            },
        ),
        migrations.AddField(
            model_name='clientes',
            name='qtdcontrato',
            field=models.IntegerField(null=True),
        ),
    ]
