from django.conf import settings
from app_cg.models import Empresas
from .Template import Template
from .ContratosC import ContratosC

class Empresa:
    def __init__(self,codempresa=0,nome=None,razaosocial=None,cnpj=None):
        self.codempresa=codempresa
        self.nome=nome
        self.razaosocial = razaosocial
        self.cpnj = cnpj
    
    def obterTodasEmpresas(self): # Usuário administrador obtém todas as empresas
        return list(Empresas.objects.filter())
    
    def atualizarEmpresa(self):
        empresa_obj = Empresas.objects.filter(codempresa=self.codempresa).first()
        empresa_obj.nome = self.nome
        empresa_obj.razaosocial = self.razaosocial
        empresa_obj.cnpj = self.cpnj
        empresa_obj.save()

    def salvarEmpresa(self):
        empresa_obj = Empresas(nome=self.nome,razaosocial=self.razaosocial,cnpj=self.cpnj)
        empresa_obj.save()
    
    def excluirEmpresa(self):
        t = Template().obterTemplates(self.codempresa)
        c = ContratosC().obterContratos(self.codempresa)
        if t or c:
            return False # Não pode excluir a empresa, pois existem templates ou contratos vinculados a ela
        empresa_obj = Empresas.objects.filter(codempresa=self.codempresa).first()
        empresa_obj.delete()
        return True # Exclusão válida