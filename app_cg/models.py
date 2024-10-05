from django.db import models

# Create your models here.
class Empresas(models.Model):
    codempresa = models.AutoField(primary_key=True)
    nome = models.TextField(max_length=100, default='Empresa')
    razaosocial = models.TextField(max_length=100, default='Razao')
    cnpj = models.TextField(max_length=1, default='CNPJ')

class Usuarios(models.Model):
    codusuario = models.AutoField(primary_key=True)
    codempresa = models.ForeignKey(Empresas, on_delete=models.CASCADE)
    nome = models.TextField(max_length=100, default='Nome')
    email = models.TextField(max_length=100, null=True)
    login = models.TextField(max_length=100, default='Login')
    senha = models.TextField(max_length=100, default='Senha')

class Clientes(models.Model):
    codcliente = models.AutoField(primary_key=True)
    nome = models.TextField(max_length=100, default='Cliente')
    telefone = models.TextField(max_length=100, null=True)
    endereco = models.TextField(max_length=100, null=True)
    cpf = models.TextField(max_length=14, null=True)

class Contrato(models.Model):
    codcontrato = models.AutoField(primary_key=True)
    codcliente = models.ForeignKey(Clientes, on_delete=models.CASCADE, null=True)
    codusuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True)
    tipocontrato = models.TextField(max_length=1, default='X')
    status = models.TextField(max_length=1, default='A')
    dtcriacao = models.TextField(max_length=10, null=True)
    dtatualiz = models.TextField(max_length=10, null=True)
    enderecoevento = models.TextField(max_length=100, null=True)
    dtevento = models.TextField(max_length=10, null=True)
    mesasinclusas = models.TextField(max_length=100, null=True)
    mesasqavulsas = models.TextField(max_length=100, null=True)
    mesasravulsas = models.TextField(max_length=100, null=True)
    cadeirasavulsas = models.TextField(max_length=100, null=True)
    toalhasavulsas = models.TextField(max_length=100, null=True)
    horaentrada = models.TextField(max_length=10, null=True)
    horasaida = models.TextField(max_length=10, null=True)
    tipoevento = models.TextField(max_length=20, null=True)
    qtdconvidados = models.TextField(max_length=100, null=True)
    valortotal = models.TextField(max_length=20, null=True)
    valorsinal = models.TextField(max_length=20, null=True)
    valordeslocamento = models.TextField(max_length=20, null=True)

class Tipositensadicionais(models.Model):
    codtipoitem = models.AutoField(primary_key=True)
    tipocontrato = models.TextField(max_length=1, default='X')
    nome = models.TextField(max_length=100, default='Itens')

class Itensadicionais(models.Model):
    coditem = models.AutoField(primary_key=True)
    codcontrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, default=0)
    codtipoitem = models.ForeignKey(Tipositensadicionais, on_delete=models.CASCADE, default=0)
    nome = models.TextField(max_length=100, default='Item')
    dtatualiz = models.TextField(max_length=10, null=True)

class Teste(models.Model):
    nome = models.TextField(null=True)
    telefone = models.TextField(null=True)
    teste = models.TextField(default='teste_criando_nova_coluna')

def __str__(self):
    return self.name