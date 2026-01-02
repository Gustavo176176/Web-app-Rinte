⚡ Web-app Rinte — Plataforma de Gestão de Consumos Residenciais

🧩 Visão Geral

Aplicação web desenvolvida no âmbito do Mestrado em Engenharia Eletrotécnica e de Computadores — Automação e Sistemas do ISEP, para gerir, organizar e analisar consumos residenciais,como água, luz e gás.

O objetivo é fornecer ao utilizador um painel simples, centralizado e web-friendly, onde pode inserir consumos, consultar históricos e identificar padrões que ajudam a reduzir desperdícios e melhorar a eficiência no ambiente doméstico, através de gráficos e documentos.

✨ Funcionalidades

.Registo de consumos por data, categoria ou dispositivo.

.Histórico detalhado, com listagem e pesquisa.

.Visualizações gráficas para análise de tendências mensais e anuais.

.Filtros avançados para análise por período.

🛠️ Arquitectura e Tecnologias Backend

Linguagem: Python

Framework: Django

Base de dados: MySQL

Arquitetura MTV do Django, com separação entre models, views e templates.

Frontend

Visualização de dados: Chart.js

Estrutura HTML/CSS : Bootstrap

🚀 Instalação e Execução Local

Importar o repositório

 git clone https://github.com/Gustavo176176/Web-app-Rinte.git
 cd Web-app-Rinte
2.Configurar o ambiente virtual:

	  python -m venv venv
	  source venv/bin/activate       # Linux/macOS
	  venv\Scripts\activate          # Windows

	pip install -r requirements.txt
Configurar a base de dados MySQL

.Criar uma base de dados vazia no MySQL.

.Atualizar as credenciais no ficheiro de configuração do Django

.Executar migrações:

 	  python manage.py migrate
Inicar o servidor:

    python manage.py runserver

LinkdIN: https://www.linkedin.com/in/gustavo-marques-3346a9242/
