from app_cg.models import Variaveis
from django.core.files.storage import default_storage
from datetime import datetime

class Variavel:
    INICIA_COLUNA = '<div class="row">'
    FECHA_COLUNA = '</div>'
    def __init__(self, codvariavel=0, codtemplate=0, variaveis=None, dtatualiz=datetime.now(), status=1):
        self.codvariavel = codvariavel 
        self.codtemplate = codtemplate 
        self.variaveis = variaveis 
        self.dtatualiz = dtatualiz 
        self.status = status
    
    def obterVariavelCompletaPorCodtemplate(self):
        variavel_obj = Variaveis.objects.filter(codtemplate=self.codtemplate).first()
        if variavel_obj:
            self.codtemplate = variavel_obj.codtemplate
            self.codvariavel = variavel_obj.codvariavel
            self.variaveis = variavel_obj.variaveis
            self.dtatualiz = variavel_obj.dtatualiz
            self.status = variavel_obj.status
        return variavel_obj
    
    def obterVariavel(self, codtemplate):
        if codtemplate:
            variavel_obj = Variaveis.objects.filter(codtemplate=codtemplate).first()
            return variavel_obj
    
    def salvarVariavel(self):
        from .Template import Template
        variavel_obj = Variaveis(codtemplate=Template().obterObjetoTemplateSemCodempresa(self.codtemplate), 
                                 variaveis=self.variaveis, dtatualiz=datetime.now(), status=1)
        variavel_obj.save()

    def excluirVariavel(self):
        variavel_obj = self.obterVariavel(self.codtemplate)
        if variavel_obj:
            variavel_obj.delete()
    
    def GerarForularioDinamico(self):
        html_string = ""
        contador_lista = 0
        organiza_em_coluna = 0
        listas_enumeradas = 0
        variaveis_ja_mostradas = []
        # percorrer variáveis e construir o formulário em html
        if self.variaveis:
            html_string += f"""
                            <div class="mb-3">
                                <label for="nome_arquivo_finale" class="form-label">Nome do arquivo</label>
                                <div class="input-group">
                                    <span class="input-group-text">abc</span>
                                    <input type="text" class="form-control" name="nome_arquivo_finale" id="nome_arquivo_finale" placeholder="Nome do Arquivo" required>
                                    <div id="nome-erro" class="invalid-feedback" style="display: none;">Campo obrigatório!</div>
                                </div>
                            </div>
                        """
            for v in self.variaveis:
                nome_var = str(v.get('nome')).strip().capitalize()
                descricao_var = str(v.get('descricao')).strip().capitalize()
                tipo_var = str(v.get('tipo')).lower().strip()
                coluna_auxiliar = ''
                # Verificar se a variável já foi apresentada na tela
                if nome_var in variaveis_ja_mostradas:
                    continue  # Pula para a próxima variável se já foi mostrada
                # Mostra a variável na tela
                if tipo_var == 'palavra' or  tipo_var == 'palavrasemlinha':
                    if nome_var == 'Telefone' or nome_var == 'Celular':
                        tipoTelefone = '(00) 0000-0000' if nome_var == 'Telefone' else '(00) 0 0000-0000'
                        if organiza_em_coluna == 0:
                            html_string += self.INICIA_COLUNA
                            organiza_em_coluna = 1
                        else:
                            coluna_auxiliar = self.FECHA_COLUNA
                            organiza_em_coluna = 0
                        html_string += f""" 
                            <div class="mb-3 col-md-6">
                                <label for="{nome_var}" class="form-label">{descricao_var}</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-phone"></i></span>
                                    <input type="tel" class="form-control" name="{nome_var}" id="{nome_var.lower()}" maxlength="15" placeholder="{tipoTelefone}">
                                    <div id="phone-error" class="invalid-feedback" style="display: none;">Número de {nome_var.lower()} inválido! Estão faltando dígitos.</div>
                                </div>
                            </div>
                        """ + coluna_auxiliar
                    elif nome_var == 'Cpf':
                        if organiza_em_coluna == 0:
                            html_string += self.INICIA_COLUNA
                            organiza_em_coluna = 1
                        else:
                            coluna_auxiliar = self.FECHA_COLUNA
                            organiza_em_coluna = 0
                        html_string += f"""
                            <div class="mb-3 col-md-6">
                                <label for="cpf" class="form-label">CPF</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-user"></i></span>
                                    <input type="text" class="form-control" name="Cpf" id="cpf" placeholder="000.000.000-00">
                                    <div id="cpf-error" class="invalid-feedback" style="display: none;">CPF inválido! Estão faltando dígitos.</div>
                                </div>
                            </div>
                        """ + coluna_auxiliar
                    else:
                        if organiza_em_coluna == 1:
                            coluna_auxiliar = self.FECHA_COLUNA
                            html_string += coluna_auxiliar
                        organiza_em_coluna = 0
                        html_string += f"""
                            <div class="mb-3">
                                <label for="{nome_var}" class="form-label">{descricao_var}</label>
                                <div class="input-group">
                                    <span class="input-group-text">abc</span>
                                    <input type="text" class="form-control" name="{nome_var}" id="{nome_var}" placeholder="{descricao_var}">
                                </div>
                            </div>
                        """
                elif tipo_var == 'inteiro':
                    if organiza_em_coluna == 0:
                        html_string += self.INICIA_COLUNA
                        organiza_em_coluna = 1
                    else:
                        coluna_auxiliar = self.FECHA_COLUNA
                        organiza_em_coluna = 0
                    html_string += f"""
                        <div class="mb-3 col-md-6">
                            <label for="{nome_var}" class="form-label">{descricao_var}</label>
                            <div class="input-group">
                                <span class="input-group-text">123</span>
                                <input type="number" class="form-control" name="{nome_var}" id="{nome_var}">
                            </div>
                        </div>
                    """ + coluna_auxiliar

                elif tipo_var == 'data':
                    if organiza_em_coluna == 0:
                        html_string += self.INICIA_COLUNA
                        organiza_em_coluna = 1
                    else:
                        coluna_auxiliar = self.FECHA_COLUNA
                        organiza_em_coluna = 0
                    html_string += f"""
                        <div class="mb-3 col-md-6">
                            <label for="{nome_var}" class="form-label">{descricao_var}</label>
                            <input type="date" class="form-control" name="{nome_var}" id="{nome_var}">
                        </div>
                    """ + coluna_auxiliar

                elif tipo_var == 'hora':
                    if organiza_em_coluna == 0:
                        html_string += self.INICIA_COLUNA
                        organiza_em_coluna = 1
                    else:
                        coluna_auxiliar = self.FECHA_COLUNA
                        organiza_em_coluna = 0
                    html_string += f"""
                        <div class="mb-3 col-md-6">
                            <label for="{nome_var}" class="form-label">{descricao_var}</label>
                            <input type="time" class="form-control" name="{nome_var}" id="{nome_var}">
                        </div>
                    """ + coluna_auxiliar

                elif tipo_var == 'moeda':
                    if organiza_em_coluna == 0:
                        html_string += self.INICIA_COLUNA
                        organiza_em_coluna = 1
                    else:
                        coluna_auxiliar = self.FECHA_COLUNA
                        organiza_em_coluna = 0
                    html_string += f"""
                        <div class="mb-3 col-md-6">
                            <label for="{nome_var}" class="form-label">{descricao_var}</label>
                            <div class="input-group">
                                <span class="input-group-text">R$</span>
                                <input type="text" class="form-control" name="{nome_var}" id="{nome_var}" placeholder="0,00">
                            </div>
                        </div>
                        <script>
                            new Cleave('#{nome_var}', {{
                                numeral: true,
                                numeralDecimalMark: ',',
                                delimiter: '.',
                                numeralThousandsGroupStyle: 'thousand'
                            }});
                        </script>
                    """ + coluna_auxiliar

                elif tipo_var == 'listaenumerada':
                    listas_enumeradas += 1
                    contador_lista += 1
                    html_string += f"""
                        <input type="hidden" name="listaenumerada-{listas_enumeradas}" id="listaenumerada-{listas_enumeradas}" value="{nome_var}">
                        <div class="mb-3">
                            <div id="inputContainer">
                                <label class="form-label">{descricao_var}</label>
                                <div class="inputGroup mb-3">
                                    <div class="input-group">
                                        <button class="btn btn-danger" type="button"
                                            onclick="removeInput(this)">x</button>
                                        <input type="text" class="form-control" name="{nome_var}-1" placeholder="Digite o item">
                                    </div>
                                </div>
                            </div>
                                <button type="button" class="btn btn-outline-success" onclick="addInput()">Acrescentar um item</button>
                        </div>

                        <script>
                            let inputCount = 1;

                            function addInput() {{
                                inputCount++;

                                // Cria um novo div para o grupo de input
                                const newInputGroup = document.createElement('div');
                                newInputGroup.className = 'inputGroup mb-3';

                                // Cria o input-group do Bootstrap
                                const inputGroupDiv = document.createElement('div');
                                inputGroupDiv.className = 'input-group';

                                // Cria o botão de excluir
                                const deleteButton = document.createElement('button');
                                deleteButton.setAttribute('type', 'button');
                                deleteButton.className = 'btn btn-danger';
                                deleteButton.textContent = 'x';
                                deleteButton.onclick = function () {{
                                    removeInput(deleteButton);
                                }};

                                // Cria o novo input
                                const newInput = document.createElement('input');
                                newInput.setAttribute('type', 'text');
                                newInput.setAttribute('placeholder', 'Digite o item')
                                newInput.setAttribute('name', '{nome_var}-' + inputCount);
                                newInput.setAttribute('id', '{nome_var}-' + inputCount);
                                newInput.className = 'form-control'; // Classe Bootstrap para input

                                // Adiciona o input e o botão dentro do input-group
                                inputGroupDiv.appendChild(deleteButton);
                                inputGroupDiv.appendChild(newInput);

                                // Adiciona o input-group ao container de inputs
                                newInputGroup.appendChild(inputGroupDiv);

                                const inputContainer = document.getElementById('inputContainer');
                                inputContainer.appendChild(newInputGroup);
                            }}

                            function removeInput(button) {{
                                // Remove o grupo de input que contém o botão de excluir
                                const inputGroup = button.closest('.inputGroup');
                                inputGroup.remove();
                            }}
                        </script>
                        """
                elif tipo_var == 'listacomtitulo----': # Por enquanto desativado
                    contador_lista += 1
                    html_string += f"""
                        <div class="mb-4" style:"display: None;">
                            <p>{descricao_var}</p>
                            <div id="ContainerTitulos-{contador_lista}">
                                <!-- Aqui os títulos e campos serão adicionados dinamicamente -->
                            </div>

                            <div class="col-12 mt-3 text-end d-flex gap-1">
                                <button type="button" class="btn custom-primary-link btn-sm" onclick="addTitle()">Novo Título</button>
                            </div>
                        </div>

                        <script>
                            let titleCount = 0;
                            let itemCount = 0;

                            function addTitle() {{
                                titleCount++;

                                // Cria o container do título
                                const titleDiv = document.createElement('div');
                                titleDiv.className = 'titleGroup mb-3';
                                titleDiv.setAttribute('data-title-id', titleCount);

                                // Cria o input do título
                                const titleInputGroup = document.createElement('div');
                                titleInputGroup.className = 'input-group mb-2';

                                const titleInput = document.createElement('input');
                                titleInput.type = 'text';
                                titleInput.placeholder = 'Digite o título';
                                titleInput.name = 'titulo' + titleCount;
                                titleInput.id = 'titulo' + titleCount;
                                titleInput.className = 'form-control';

                                const deleteTitleBtn = document.createElement('button');
                                deleteTitleBtn.type = 'button';
                                deleteTitleBtn.className = 'btn btn-danger btn-sm';
                                deleteTitleBtn.textContent = 'x';
                                deleteTitleBtn.onclick = function () {{
                                    titleDiv.remove();
                                }};

                                titleInputGroup.appendChild(deleteTitleBtn);
                                titleInputGroup.appendChild(titleInput);

                                // Container para os campos desse título
                                const fieldsContainer = document.createElement('div');
                                fieldsContainer.className = 'ms-4'; // Aninhamento visual (tab)
                                fieldsContainer.id = 'fieldsContainer' + titleCount;

                                // Botão para adicionar campos
                                const addFieldBtn = document.createElement('button');
                                addFieldBtn.type = 'button';
                                addFieldBtn.className = 'btn custom-primary-link btn-sm mt-2 ms-4';
                                addFieldBtn.textContent = 'Item';
                                addFieldBtn.onclick = function () {{
                                    addField(fieldsContainer.id, titleCount);
                                }};

                                // Monta o título com seus campos
                                titleDiv.appendChild(titleInputGroup);
                                titleDiv.appendChild(fieldsContainer);
                                titleDiv.appendChild(addFieldBtn);

                                document.getElementById('ContainerTitulos-{contador_lista}').appendChild(titleDiv);

                                // Adiciona o primeiro campo automaticamente
                                addField(fieldsContainer.id, titleCount);
                            }}

                            function addField(containerId, titleCount) {{
                                itemCount++;
                                const container = document.getElementById(containerId);

                                const fieldGroup = document.createElement('div');
                                fieldGroup.className = 'inputGroup mb-2';

                                const inputGroupDiv = document.createElement('div');
                                inputGroupDiv.className = 'input-group';

                                const deleteButton = document.createElement('button');
                                deleteButton.type = 'button';
                                deleteButton.className = 'btn btn-danger btn-sm';
                                deleteButton.textContent = 'x';
                                deleteButton.onclick = function () {{
                                    fieldGroup.remove();
                                }};

                                const newInput = document.createElement('input');
                                newInput.type = 'text';
                                newInput.placeholder = 'Digite o item';
                                newInput.name = 'item-'+itemCount+'-titulo-'+titleCount+'-lista-'+{contador_lista};
                                newInput.id = 'item-'+itemCount+'-titulo-'+titleCount+'-lista-'+{contador_lista};
                                newInput.className = 'form-control';

                                inputGroupDiv.appendChild(deleteButton);
                                inputGroupDiv.appendChild(newInput);
                                fieldGroup.appendChild(inputGroupDiv);

                                container.appendChild(fieldGroup);
                            }}
                        </script>
                    """
                variaveis_ja_mostradas.append(nome_var)
        # Caso o template não tenha nenhuma variável
        if html_string == "":
            html_string += """
                <div class="text-center mb-5 fst-italic fw-light">
                    <p>Nenhuma variável encontrada para este template.</p>
                </div>
            """

        # Acrescentar máscara de CPF e Telefone, caso tenha
        html_string += """
            <script>
                $(document).ready(function () {
                    // Aplica a máscara ao campo de telefone e CPF
                    $('#telefone').mask('(00) 0 0000-0000');
                    $('#cpf').mask('000.000.000-00');

                    // Função para validar o telefone
                    function validarTelefone() {
                        var phoneNumber = $('#telefone').val();

                        // Verifica se o Telefone está vazio
                        if (phoneNumber === '') {
                            $('#phone-error').hide();
                            $('#telefone').removeClass('is-invalid').removeClass('is-valid'); // Remove classes de validação
                            return true; // Permite o envio do formulário
                        }

                        // Verifica se o número tem exatamente 16 caracteres (formato completo)
                        if (phoneNumber.length !== 16) {
                            $('#phone-error').show();
                            $('#telefone').addClass('is-invalid');
                            return false;
                        } else {
                            $('#phone-error').hide();
                            $('#telefone').removeClass('is-invalid').addClass('is-valid');
                            return true;
                        }
                    }

                    // Função para validar o CPF
                    function validarCPF() {
                        var cpfNumber = $('#cpf').val();

                        // Verifica se o CPF está vazio
                        if (cpfNumber === '') {
                            $('#cpf-error').hide();
                            $('#cpf').removeClass('is-invalid').removeClass('is-valid'); // Remove classes de validação
                            return true; // Permite o envio do formulário
                        }

                        // Verifica se o CPF tem exatamente 14 caracteres (formato completo)
                        if (cpfNumber.length !== 14) {
                            $('#cpf-error').show();
                            $('#cpf').addClass('is-invalid');
                            return false;
                        } else {
                            $('#cpf-error').hide();
                            $('#cpf').removeClass('is-invalid').addClass('is-valid');
                            return true;
                        }
                    }

                    // Previne o envio do formulário se o telefone ou CPF forem inválidos
                    $('#myForm').on('submit', function (e) {
                        var validPhone = validarTelefone();
                        var validCPF = validarCPF();

                        if (!validPhone || !validCPF) {
                            e.preventDefault(); // Previne o envio do formulário
                            return false;
                        }
                    });

                    // Validação contínua enquanto o usuário digita (corrige o erro enquanto ele digita)
                    $('#telefone').on('input', function () {
                        validarTelefone();
                    });

                    $('#cpf').on('input', function () {
                        validarCPF();
                    });
                });
            </script>
        """
        return html_string