from app_cg.models import Contratos
from django.conf import settings
import json, re, datetime
from django.core.files.storage import default_storage
from docx import Document
from io import BytesIO
from docx.text.run import Run
from docx.enum.text import WD_BREAK
from .Definicoes import Definicoes

class ContratosC:
    def __init__(self, codcontrato=None,codusuario=None,codtemplate=None,codempresa=None,nome_arquivo=None,contrato_url=None,contrato_json=None,status=None,dtatualiz=None):
        self.codcontrato = codcontrato 
        self.codusuario = codusuario 
        self.codtemplate = codtemplate 
        self.codempresa = codempresa
        self.nome_arquivo = nome_arquivo
        self.contrato_url = contrato_url 
        self.contrato_json = contrato_json 
        self.status = status 
        self.dtatualiz = dtatualiz 
    
    def obterContratos(self, codempresa, codcontrato=None):
        if codcontrato is None:
            # Se o codcontrato for None, então retorna uma lista de contratos da empresa selecionada
            return list(Contratos.objects.filter(codempresa=codempresa))
        # Se o codcontrato estiver preenchido, então retorna o Objeto contrato, se não, vai retornar None
        # Realiza também tratativa de filtrar apenas documentos da empresa do usuário logado
        contrato_obj = Contratos.objects.filter(codempresa=codempresa, codcontrato=codcontrato).first()
        if contrato_obj is None: return contrato_obj # Se o contrato não for encontrado, então retorna None
        self.codcontrato = contrato_obj.codcontrato
        self.codusuario = contrato_obj.codusuario
        self.codtemplate = contrato_obj.codtemplate
        self.codempresa = contrato_obj.codempresa
        self.nome_arquivo = contrato_obj.nome_arquivo
        self.contrato_url = contrato_obj.contrato_url
        self.contrato_json = contrato_obj.contrato_json
        self.status = contrato_obj.status
        self.dtatualiz = contrato_obj.dtatualiz
        return contrato_obj
    
    def obterArquivoContrato(self):
        # Sempre usar rb (read binary) para arquivos binários, como .docx. 
        with default_storage.open(self.contrato_url, "rb") as arquivo:
            return arquivo

    def gerarContrato(self):
        # Capturar o template
        with default_storage.open(self.codtemplate.template_url, "rb") as arquivo:
            doc = Document(arquivo)

        # Regex para identificar as expressões no formato <?tipo:nome:descricao?>
        padrao = r"<\?([a-zA-Z0-9_]+):([a-zA-Z0-9_]+):.*?\?>"

        doc = substituir_variaveis_docx(doc, self.contrato_json)
        
        # # Processando os parágrafos do DOCX
        # for p in doc.paragraphs: # Percorrer cada parágrafo do template
        #     matches = re.findall(padrao, p.text)  # Encontrar todas as expressões de variáveis
        #     for tipo, nome in matches: # Coletar o tipo e o nome das variáveis
        #         # É preciso formatar o nome da variável, porque isso foi tratado na hora de enviar os nomes para o template HTML:
        #         nome_formatado = trataNomeVariavel(nome)
        #         # Percorrer a lista dos dados no JSON
        #         if nome_formatado in self.contrato_json.get("dados_json", {}):
        #             # print(f"\nNome da variável: {nome_formatado};")
        #             # Se algum dos dados do JSON não estiver preenchido, substituir por traços que permitirá o cliente preencher à caneta:
        #             if tipo == "data":
        #                 valor = ifnull(transformaData(self.contrato_json["dados_json"][nome_formatado]), '___ / ___ / _____')
        #             elif tipo == "listacomtitulo":
        #                 valor = ifnull(self.contrato_json["dados_json"][nome_formatado], '')
        #             else:
        #                 valor = ifnull(self.contrato_json["dados_json"][nome_formatado], '______________________________')
        #             # Substituir a expressão da variável, no template, pelo valor informado no formulário
        #             p.text = re.sub(rf"<\?{tipo}:{nome}:.*?\?>", valor, p.text)
                    
        # # CONVERTER PARA PDF COM LIBREOFFICE --> Isso não funciona na Vercel, precisaria de um servidor como EC2 ou Docker
        # subprocess.run([
        #     "soffice", 
        #     "--headless",  # Sem interface gráfica
        #     "--convert-to", 
        #     "pdf",  # Converter para PDF
        #     modified_docx_path
        # ], check=True)

        # Salvar o DOCX gerado em memória para o S3
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        # Salvar os dados do contrato no banco de dados
        contrato_obj = Contratos(codusuario=self.codusuario,codtemplate=self.codtemplate,codempresa=self.codempresa,
                                 contrato_json=self.contrato_json,nome_arquivo=self.nome_arquivo,status=self.status,
                                 dtatualiz=self.dtatualiz)
        contrato_obj.save() # Salvar o objeto contrato no banco de dados
        self.codcontrato = contrato_obj.codcontrato # Coletar o código do contrato que acabou de ser salvo
        caminho = default_storage.save(self.criarCaminhoContrato(), buffer) # Salvar o arquivo na nuvem do S3
        contrato_obj.contrato_url = str(caminho) # Guardar o caminho do S3 no banco de dados
        contrato_obj.save() # Atualizar o registro do caminho do contrato no banco de dados
        print(f'DEBUG: contrato salvo!\ncaminho: {caminho}')
        if caminho: 
            return True 
        return False # Se não conseguiu salvar o arquivo, retorna False e mostra erro na tela do usuário

    def criarCaminhoContrato(self): # Obtém o caminho do novo contrato na nuvem do S3
        caminho_inicial = 'HOMOLOGACAO' if settings.DEBUG else 'PRODUCAO'
        caminho_final = f'contratos/empresa_{self.codusuario.codempresa.codempresa}/{self.codcontrato}.docx'
        return f'{caminho_inicial}/{caminho_final}'
    
    def existeContratoGeradoPeloCodtemplate(self, codtemplate): # Verifica se existe contrato gerado a partir do código do template informado
        contrato_obj = Contratos.objects.filter(codtemplate=codtemplate).first()
        if contrato_obj is None:
            return False
        return True
    
def ifnull(x, y):
    if x is not None and x != "" and x != " ":
        return x
    else:
        return y
    
def transformaData(data_str):
    try:
        data = datetime.datetime.strptime(data_str, "%Y-%m-%d")
    except ValueError:
        return None
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    return f"{data.day} de {meses[data.month - 1]} de {data.year}"

def trataNomeVariavel(nome):
    nome = str(nome)
    return nome.capitalize()

def substituir_variaveis_docx(doc, contrato_json):
    padrao = re.compile(r"<\?([^:<>]+):([^:<>]+):[^<>]*\?>")  # <?tipo:nome:descricao?>
    
    for p in doc.paragraphs:
        _processar_paragrafo(p, padrao, contrato_json)

    # Percorrer todas as tabelas
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for p in celula.paragraphs:
                    _processar_paragrafo(p, padrao, contrato_json)
    
    return doc


def _processar_paragrafo(p, padrao, contrato_json):
    matches = re.findall(padrao, p.text)
    for tipo, nome in matches:
        nome_formatado = trataNomeVariavel(nome)
        dado = contrato_json["dados_json"][nome_formatado]

        if nome_formatado in contrato_json.get("dados_json", {}):
            if tipo not in Definicoes.TIPOS_PERMITIDOS:
                continue # Pular tipos não permitidos
            elif tipo == "data":
                valor = ifnull(transformaData(dado), '___ / ___ / _____')
            # elif tipo == "listacomtitulo":
            #     valor = ifnull(dado, '')
            elif tipo == "listaenumerada":
                if isinstance(dado, list) and dado:
                    lista_itens = [item for sub in dado for item in (sub if isinstance(sub, list) else [sub])]
                    texto_paragrafo = ''.join(run.text for run in p.runs)
                    padrao = rf"<\?{tipo}:{nome}:.*?\?>"
                    match = re.search(padrao, texto_paragrafo)
                    # Substituir o placeholder por uma lista numerada com quebras reais
                    
                    if match:
                        # Limpa todo o parágrafo
                        for run in p.runs:
                            run.text = ""
                        # Adiciona a lista formatada
                        for idx, item in enumerate(lista_itens):
                            new_run = p.add_run(f"  {idx + 1}. {item}")
                            new_run.add_break(WD_BREAK.LINE)
                        continue
                else:
                    valor = ''
            else:
                valor = ifnull(dado, '______________________________')

            # Substitui o texto da variável pelo valor
            valor = str(valor)
            p.text = re.sub(rf"<\?{tipo}:{nome}:.*?\?>", valor, p.text)