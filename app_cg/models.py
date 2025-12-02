from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

import pyotp

def validar_extensao_docx(arquivo):
    if not arquivo.name.endswith('.docx'):
        raise ValidationError('Apenas arquivos .docx são permitidos.')
def caminho_template(instancia, nomearquivo):
    return f'templates/empresa_{instancia.codempresa.codempresa}/{nomearquivo}'

##### Em caso de alteração no model, é necessário rodar os comandos de migração de 
##### Banco de dados. Como o projeto possui dois bancos de homologação e um de pro-
##### dução, para atualizar todos, pode alterar o link de acesso no arquivo ".env"
##### e rodar os comandos abaixo para cada conexão, mudando os links sempre com 
##### o endereço "pools". Depois disso, retornar para o link de homologação local.

##### OBS.: Caso faça migração do banco de produção de dentro do ambiente de homologação
##### local, poderá ser necessário promover a branch para produção logo em seguida.

## python manage.py makemigrations
## python manage.py migrate

class Empresas(models.Model):
    codempresa = models.AutoField(primary_key=True)
    nome = models.TextField(max_length=100, default='Empresa')
    razaosocial = models.TextField(max_length=100, default='Razao')
    cnpj = models.TextField(max_length=1, default='CNPJ')


class Usuarios(models.Model):
    codusuario = models.AutoField(primary_key=True)
    codempresa = models.ForeignKey('Empresas', on_delete=models.CASCADE)
    nome = models.TextField(max_length=100, default='Nome')
    email = models.TextField(max_length=100, null=True)
    login = models.TextField(max_length=100, default='Login')
    senha = models.TextField(max_length=100, default='Senha')
    permissoes = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'),
        ('gestor', 'Gestor'),
        ('colaborador', 'Colaborador'),
    ], default='colaborador')
    dois_fatores = models.BooleanField(default=False)  # Agora começa desativado
    utiliza_dois_fatores = models.BooleanField(default=True)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)

    def gerar_otp_secret(self):
        """Gera um segredo único para o 2FA se ainda não existir"""
        if not self.otp_secret:
            self.otp_secret = pyotp.random_base32()
            self.save()
        return self.otp_secret

class Templates(models.Model):
    codtemplate = models.AutoField(primary_key=True)
    codempresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, null=False)
    nome = models.TextField(max_length=100, default='Template')
    descricao = models.TextField(max_length=255, default='')
    template_url = models.TextField(default='Template')
    dtatualiz = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True) # 0 para Inativo e 1 para Ativo
    # INDEXs para a tabela Templates
    # CREATE INDEX idx_templates_01 ON app_cg_templates(codtemplate);
    # CREATE INDEX idx_templates_02 ON app_cg_templates(codempresa_id);
    # CREATE INDEX idx_templates_03 ON app_cg_templates(codempresa_id, status);
    class Meta:
        indexes = [
            models.Index(fields=['codtemplate']),          # índice simples
            models.Index(fields=['codempresa']),  # índice composto
            models.Index(fields=['codempresa', 'status']),  # índice composto
        ]

class V_Templates_codnomedtatualiz(models.Model):
    codtemplate = models.AutoField(primary_key=True)
    codempresa_id = models.IntegerField(null=True)
    nome = models.TextField(max_length=100, default='Template')
    dtatualiz = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True) # 0 para Inativo e 1 para Ativo

    class Meta:
        managed = False  # Django não tentará criar, modificar ou deletar essa view
        db_table = 'view_templates_codnomedtatualiz'  # Nome da view no banco de dados
            #CREATE OR REPLACE VIEW VIEW_TEMPLATES_CODNOMEDTATUALIZ AS
            #SELECT CODTEMPLATE, CODEMPRESA_ID, NOME, DTATUALIZ, STATUS FROM APP_CG_TEMPLATES

class Variaveis(models.Model):
    codvariavel = models.AutoField(primary_key=True)
    codtemplate = models.ForeignKey(Templates, on_delete=models.CASCADE, null=False)
    variaveis = models.JSONField(null=True) #ex: [{"nome":"var1", "descricao":"var1", "tipo":1}, {"nome":"var2", "descricao":"var2", "tipo":2}, {...}}]
    dtatualiz = models.DateTimeField(null=True, blank=True)
    status = status = models.IntegerField(null=True) # 0 para Inativo e 1 para Ativo

class Contratos(models.Model):
    codcontrato = models.AutoField(primary_key=True)
    codusuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True, blank=True)
    codtemplate = models.ForeignKey(Templates, on_delete=models.CASCADE, null=False)
    codempresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, null=False)
    nome_arquivo = models.TextField(default='')
    contrato_url = models.TextField(default='Contrato')
    contrato_json = models.JSONField(blank=True, null=True)
    status = status = models.IntegerField(null=True) # 0 para Inativo e 1 para Ativo
    dtatualiz = models.DateTimeField(null=True, blank=True)
    # INDEXs para a tabela Contratos
    # CREATE INDEX idx_contratos_01 ON app_cg_contratos(codcontrato);
    # CREATE INDEX idx_contratos_02 ON app_cg_contratos(codempresa);
    # CREATE INDEX idx_contratos_03 ON app_cg_contratos(codempresa, codcontrato);
    class Meta:
        indexes = [
            models.Index(fields=['codcontrato']),          # índice simples
            models.Index(fields=['codempresa']),  # índice composto
            models.Index(fields=['codempresa', 'codcontrato']),  # índice composto
        ]
    
class V_BuscaContratos(models.Model):
    codcontrato = models.AutoField(primary_key=True)
    codempresa = models.IntegerField(null=True)
    codtemplate = models.IntegerField(null=True)
    nometemplate = models.TextField(max_length=100)
    nome_arquivo = models.TextField(max_length=100)
    contrato_url = models.TextField(max_length=100)
    dtatualiz = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False  # Django não tentará criar, modificar ou deletar essa view
        db_table = 'view_lista_contratos'  # Nome da view no banco de dados
        # CREATE OR REPLACE VIEW view_lista_contratos AS
        # SELECT C.CODCONTRATO, C.CODEMPRESA_ID AS CODEMPRESA, T.CODTEMPLATE, 
        #     T.NOME AS NOMETEMPLATE, C.NOME_ARQUIVO, C.CONTRATO_URL, C.DTATUALIZ
        # FROM APP_CG_CONTRATOS C
        # INNER JOIN APP_CG_TEMPLATES T ON T.CODTEMPLATE = C.CODTEMPLATE_ID
        # WHERE C.STATUS = 1

class V_ObterDadosContrato(models.Model):
    codcontrato = models.AutoField(primary_key=True)
    codempresa = models.IntegerField(null=True)
    contrato_json = models.JSONField(blank=True, null=True)
    nome_arquivo = models.TextField(max_length=100)

    class Meta:
        managed = False  # Django não tentará criar, modificar ou deletar essa view
        db_table = 'view_obterdadoscontrato'  # Nome da view no banco de dados
        # CREATE OR REPLACE VIEW view_obterdadoscontrato AS
        # SELECT CODCONTRATO, CODEMPRESA_ID AS CODEMPRESA, CONTRATO_JSON, NOME_ARQUIVO 
        # FROM APP_CG_CONTRATOS
        # WHERE STATUS = 1

class Clientes(models.Model):
    codcliente = models.AutoField(primary_key=True)
    nome = models.TextField(max_length=100, default='Cliente')
    telefone = models.TextField(max_length=100, null=True)
    endereco = models.TextField(max_length=100, null=True)
    cpf = models.TextField(max_length=14, null=True)
    qtdcontrato = models.IntegerField(null=True)
    dtcriacao = models.DateField(null=True)

class Contrato(models.Model):
    codcontrato = models.AutoField(primary_key=True)
    codcliente = models.ForeignKey(Clientes, on_delete=models.CASCADE, null=True)
    codusuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True)
    tipocontrato = models.TextField(max_length=1, default='X')
    status = models.TextField(max_length=1, default='A')
    dtcriacao = models.TextField(max_length=10, null=True)
    dtatualiz = models.TextField(max_length=19, null=True)
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
    dtatualiz = models.TextField(max_length=19, null=True)

class Teste(models.Model):
    nome = models.TextField(null=True)
    telefone = models.TextField(null=True)
    teste = models.TextField(default='teste_criando_nova_coluna')

class Visualizar_contratos(models.Model):
    codvcontrato = models.AutoField(primary_key=True)
    codcontrato = models.IntegerField()
    codcliente = models.IntegerField()
    nome = models.TextField(max_length=100, default='Cliente')
    dtevento = models.TextField(max_length=10, null=True)
    enderecoevento = models.TextField(max_length=100, null=True)
    tipoevento = models.TextField(max_length=20, null=True)
    status = models.TextField(max_length=1, default='A')
    tipocontrato = models.TextField(max_length=1, default='X')

    class Meta:
        managed = False  # Django não tentará criar, modificar ou deletar essa view
        db_table = 'v_visualizar_contratos'  # Nome da view no banco de dados

class Codtipoitens_itensadicionais(models.Model):
    codtipoitem = models.IntegerField()
    nome = models.TextField(max_length=100, default='Item')
    codcontrato_id = models.IntegerField()
    codvtipoitens = models.AutoField(primary_key=True)
    
    class Meta:
        managed = False  # Django não tentará criar, modificar ou deletar essa view
        db_table = 'v_codtipoitem_itensadicionais'  # Nome da view no banco de dados

def __str__(self):
    return self.name

