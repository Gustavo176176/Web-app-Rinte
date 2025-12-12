⚡ Web-app Rinte — Plataforma de Gestão de Consumos Residenciais

🧩 Visão Geral

Aplicação web desenvolvida no âmbito do Mestrado em Engenharia Eletrotécnica e de Computadores — Automação e Sistemas (ISEP), pensada para monitorizar, organizar e analisar consumos residenciais,como água, luz e gás.

O objectivo é fornecer ao utilizador um painel simples, centralizado e web-friendly, onde pode inserir consumos, consultar históricos e identificar padrões que ajudam a reduzir desperdícios e melhorar a eficiência no ambiente doméstico, através de gráficos e documentos.


✨ Funcionalidades


.Registo de consumos por data, categoria ou equipamento.

.Histórico detalhado, com listagem e pesquisa.

.Visualizações gráficas para análise de tendências mensais e anuais

.Filtros avançados para análise por período.


🛠️ Arquitectura e Tecnologias
Backend

Linguagem: Python

Framework: Django 

Base de dados: MySQL

Arquitectura MVC do Django, com separação entre models, views e templates.

Frontend

Visualização de dados: hart.js

Estrutura HTML/CSS : Bootstrap 


🚀 Instalação e Execução Local

1. Importar o repositório
   
		git clone https://github.com/Gustavo176176/Web-app-Rinte.git
		cd Web-app-Rinte

2.Configurar o ambiente virtual:


		python -m venv venv
		source venv/bin/activate       # Linux/macOS
		venv\Scripts\activate          # Windows

		pip install -r requirements.txt

3. Configurar a base de dados MySQL

	.Criar uma base de dados vazia no MySQL.

	.Atualizar as credenciais no ficheiro de configuração do Django

	.Executar migrações:
	
			python manage.py migrate
4. Inicar o servidor:

		   python manage.py runserver


📸 Exemplos
<img width="1890" height="894" alt="image" src="https://github.com/user-attachments/assets/d51ac876-82ab-407c-ad2c-b9d21b724e23" />

<img width="1918" height="904" alt="image" src="https://github.com/user-attachments/assets/acb5873a-969c-4efc-905c-d89c310b8f31" />











LinkdIN: https://www.linkedin.com/in/gustavo-marques-3346a9242/

