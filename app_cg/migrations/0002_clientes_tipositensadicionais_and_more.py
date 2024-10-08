# Generated by Django 5.0.4 on 2024-10-03 01:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cg', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clientes',
            fields=[
                ('codcliente', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.TextField(default='Cliente', max_length=100)),
                ('telefone', models.TextField(max_length=100, null=True)),
                ('endereco', models.TextField(max_length=100, null=True)),
                ('cpf', models.TextField(max_length=14, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tipositensadicionais',
            fields=[
                ('codtipoitem', models.AutoField(primary_key=True, serialize=False)),
                ('tipocontrato', models.TextField(default='X', max_length=1)),
                ('nome', models.TextField(default='Itens', max_length=100)),
            ],
        ),
        migrations.RenameField(
            model_name='empresas',
            old_name='id_empresa',
            new_name='codempresa',
        ),
        migrations.RemoveField(
            model_name='empresas',
            name='empresa',
        ),
        migrations.AddField(
            model_name='empresas',
            name='nome',
            field=models.TextField(default='Empresa', max_length=100),
        ),
        migrations.AlterField(
            model_name='empresas',
            name='cnpj',
            field=models.TextField(default='CNPJ', max_length=18),
        ),
        migrations.AlterField(
            model_name='teste',
            name='nome',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='teste',
            name='telefone',
            field=models.TextField(null=True),
        ),
        migrations.CreateModel(
            name='Contrato',
            fields=[
                ('codcontrato', models.AutoField(primary_key=True, serialize=False)),
                ('tipocontrato', models.TextField(default='X', max_length=1)),
                ('status', models.TextField(default='A', max_length=1)),
                ('dtcriacao', models.TextField(max_length=10, null=True)),
                ('dtatualiz', models.TextField(max_length=10, null=True)),
                ('enderecoevento', models.TextField(max_length=100, null=True)),
                ('dtevento', models.TextField(max_length=10, null=True)),
                ('mesasinclusas', models.TextField(max_length=100, null=True)),
                ('mesasqavulsas', models.TextField(max_length=100, null=True)),
                ('mesasravulsas', models.TextField(max_length=100, null=True)),
                ('cadeirasavulsas', models.TextField(max_length=100, null=True)),
                ('toalhasavulsas', models.TextField(max_length=100, null=True)),
                ('horaentrada', models.TextField(max_length=10, null=True)),
                ('horasaida', models.TextField(max_length=10, null=True)),
                ('tipoevento', models.TextField(max_length=20, null=True)),
                ('qtdconvidados', models.TextField(max_length=100, null=True)),
                ('valortotal', models.TextField(max_length=20, null=True)),
                ('valorsinal', models.TextField(max_length=20, null=True)),
                ('valordeslocamento', models.TextField(max_length=20, null=True)),
                ('codcliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_cg.clientes')),
            ],
        ),
        migrations.CreateModel(
            name='Itensadicionais',
            fields=[
                ('coditem', models.AutoField(primary_key=True, serialize=False)),
                ('codcontrato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_cg.contrato')),
                ('codtipoitem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_cg.tipositensadicionais')),
            ],
        ),
        migrations.CreateModel(
            name='Usuarios',
            fields=[
                ('codusuario', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.TextField(default='Nome', max_length=100)),
                ('email', models.TextField(max_length=100, null=True)),
                ('login', models.TextField(default='Login', max_length=100)),
                ('senha', models.TextField(default='Senha', max_length=100)),
                ('codempresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_cg.empresas')),
            ],
        ),
    ]
