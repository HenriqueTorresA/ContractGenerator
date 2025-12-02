class Definicoes:
    TIPOS_PERMITIDOS = ("palavra", # Para qualquer palavra. Se o nome for cpf, ou telefone, tem um tratamento especial no formulário
                        "palavrasemlinha", # Em caso da palavra estar vazia, não substitui por linha e sim remove o parágrafo
                        "inteiro", 
                        "moeda", 
                        "data", 
                        "hora", 
                        "listaenumerada" # Se tiver vazio, exclui o parágrafo inteiro
                        )