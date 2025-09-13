from app_cg.models import Variaveis
from django.core.files.storage import default_storage
from datetime import datetime

class Variavel:
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
                                 variaveis=self.variaveis, dtatualiz=self.dtatualiz, status=self.status)
        variavel_obj.save()

    def excluirVariavel(self):
        if self.codvariavel != 0:
            variavel_obj = self.obterVariavel(self.codtemplate)
            if variavel_obj:
                variavel_obj.delete()
    
    def GerarForularioDinamico(self):
        html_string = ""
        contador_lista = 0
        # percorrer variáveis e construir o formulário em html
        if self.variaveis:
            for v in self.variaveis:
                nome_var = str(v.get('nome')).strip().capitalize()
                descricao_var = str(v.get('descricao')).strip().capitalize()
                tipo_var = str(v.get('tipo')).lower().strip()
                if tipo_var == 'palavra':
                    if nome_var == 'Telefone':
                        html_string += f""" 
                            <div class="mb-3 col-md-6">
                                <label for="telefone" class="form-label">Telefone</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="bi bi-telephone"></i></span>
                                    <input type="tel" class="form-control" name="Telefone" id="telefone" maxlength="15" placeholder="(62) 9 0000-0000">
                                    <div id="phone-error" class="invalid-feedback" style="display: none;">Número de telefone inválido! Estão faltando dígitos.</div>
                                </div>
                            </div>
                        """
                    elif nome_var == 'Cpf':
                        html_string += f"""
                            <div class="mb-3 col-md-6">
                                <label for="cpf" class="form-label">CPF</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="bi bi-person-fill"></i></span>
                                    <input type="text" class="form-control" name="Cpf" id="cpf" placeholder="000.000.000-00">
                                    <div id="cpf-error" class="invalid-feedback" style="display: none;">CPF inválido! Estão faltando dígitos.</div>
                                </div>
                            </div>
                        """
                    else:
                        html_string += f"""
                            <div class="mb-3">
                                <label for="{nome_var}" class="form-label">{nome_var}</label>
                                <div class="input-group">
                                    <span class="input-group-text">abc</span>
                                    <input type="text" class="form-control" name="{nome_var}" id="{nome_var}" placeholder="{descricao_var}">
                                </div>
                            </div>
                        """
                elif tipo_var == 'inteiro':
                    html_string += f"""
                        <div class="mb-3 col-md-6">
                            <label for="{nome_var}" class="form-label">{nome_var}</label>
                            <div class="input-group">
                                <span class="input-group-text">123</span>
                                <input type="number" class="form-control" name="{nome_var}" id="{nome_var}">
                            </div>
                        </div>
                    """
                elif tipo_var == 'data':
                    html_string += f"""
                        <div class="mb-3 col-md-6">
                            <label for="{nome_var}" class="form-label">{descricao_var}</label>
                            <input type="date" class="form-control" name="{nome_var}" id="{nome_var}">
                        </div>
                    """
                elif tipo_var == 'hora':
                    html_string += f"""
                        <div class="mb-3 col-md-6">
                            <label for="{nome_var}" class="form-label">{descricao_var}</label>
                            <input type="time" class="form-control" name="{nome_var}" id="{nome_var}">
                        </div>
                    """
                elif tipo_var == 'moeda':
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
                    """
                elif tipo_var == 'listacomtitulo':
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
                # elif tipo_var == 'listaenumerada'
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