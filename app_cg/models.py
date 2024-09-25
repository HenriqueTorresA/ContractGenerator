from django.db import models

# Create your models here.
class Empresas(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    empresa = models.TextField(max_length=255)
    cnpj = models.TextField(max_length=50)

class Teste(models.Model):
    nome = models.TextField()
    telefone = models.TextField()

def __str__(self):
    return self.name