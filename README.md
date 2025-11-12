# DocFlow

Sistema de geração e gerenciamento de documentos baseados em templates pré-configurados.

## Descrição

O **DocFlow** é um sistema desenvolvido em **Django** com suporte a **PWA (Progressive Web App)**, voltado para a criação e gerenciamento automatizado de documentos corporativos.  
A aplicação permite que usuários criem **templates pré-configurados** e, a partir deles, gerem **formulários automáticos** para preenchimento dinâmico e geração dos documentos finais.  
Todo o processo é realizado com base nas diretrizes da **LGPD**, garantindo segurança e conformidade no tratamento de dados.

---

## Funcionalidades

- Gerenciamento de templates  
- Gerenciamento de documentos  
- Gerenciamento de usuários  
- Autenticação em dois fatores (2FA)  
- Controle de acesso por nível de permissão  
- Suporte a uso offline via PWA  

Esta primeira versão do sistema entrega as funcionalidades acima, com aplicação das diretrizes da LGPD.  
O sistema permite o cadastro de usuários, definição de níveis de acesso e autenticação em dois fatores para maior segurança.  

Além disso, o **DocFlow** possibilita o cadastro de templates de múltiplos documentos pré-configurados, a partir dos quais são gerados formulários automáticos que facilitam e agilizam o preenchimento e a criação dos documentos.

---

## Tecnologias Utilizadas

- **Python 3.x**
- **Django 5.x**
- **HTML5 / CSS3 / JavaScript**
- **Bootstrap 5**
- **PostgreSQL**
- **PWA (Progressive Web App)**
- **LGPD Compliance**

---

## Como Rodar o Projeto

Siga os passos abaixo para configurar e executar o projeto localmente.

### 01 - Clonar o repositório

```bash
git clone https://github.com/seuusuario/docflow.git
cd docflow

### 02 - Criar ambiente virtual
.venv\Scripts\activate

03 - Instalar dependências do projeto
pip freeze > requirements.txt

04 - Realizer migrações no banco de dados
python manage.py makemigrations
python manage.py migrate

05 - Executar o geerador de contratos
python manage.py runserver
