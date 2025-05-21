Sistema de Gerenciamento de Cronograma PPR
Aplicação web desenvolvida com Streamlit para visualização, edição e acompanhamento de metas e entregas de um cronograma de Programa de Participação nos Resultados (PPR). A aplicação integra-se com Google Sheets para armazenamento de dados e Google Drive para o upload de documentos comprobatórios.

Funcionalidades Principais
Autenticação de Usuários: Sistema de login e cadastro para acesso seguro.

Visualização de Metas: Exibição do cronograma de metas e suas respectivas entregas, filtrado pelo e-mail do usuário logado.

Filtros Avançados: Permite filtrar as metas por Referência, Setor, Responsável, Descrição da Meta e Responsável da Área.

Edição de Entregas: Usuários podem editar os campos de avaliação de cada entrega.

Upload de Documentos: Funcionalidade para anexar documentos (PDF, DOCX, XLSX, etc.) diretamente para uma pasta específica no Google Drive, associando o link à entrega correspondente na planilha.

Pré-visualização de Documentos: Exibição de uma pré-visualização de documentos do Google Drive diretamente na interface da aplicação.

Persistência de Dados: Utiliza Google Sheets como banco de dados para informações de usuários, metas e avaliações.

Estrutura do Projeto
A estrutura de pastas do projeto está organizada da seguinte forma:

SEU_PROJETO_PPR/
├── .gitignore                 # Especifica arquivos intencionalmente não rastreados pelo Git
├── app.py                     # Script principal da aplicação Streamlit (dashboard)
├── requirements.txt           # Lista de dependências Python
├── pages/                     # Diretório para as páginas secundárias da aplicação
│   ├── auth.py                # Página de autenticação (login/cadastro)
│   ├── Entrega1.py            # Página para gerenciar a Entrega 1
│   ├── Entrega2.py            # Página para gerenciar a Entrega 2
│   ├── Entrega3.py            # ... e assim por diante para as demais entregas
│   └── Entrega6.py
└── utils/                     # Diretório para módulos utilitários
    └── google_sheets.py       # Módulo para interagir com Google Sheets

Tecnologias Utilizadas
Python 3.x

Streamlit: Framework principal para a construção da interface web.

Pandas: Para manipulação e análise de dados.

gspread: Para interagir com a API do Google Sheets.

oauth2client: Para autenticação com as APIs do Google (usando conta de serviço).

google-api-python-client: Para interagir com a API do Google Drive.

Google Sheets: Utilizado como banco de dados da aplicação.

Google Drive: Utilizado para armazenamento de arquivos anexados.

Pré-requisitos
Antes de começar, garanta que você tenha o seguinte instalado e configurado:

Python: Versão 3.7 ou superior.

Git: Para clonar o repositório.

Conta Google Cloud Platform (GCP):

Um projeto criado no GCP.

API do Google Sheets e API do Google Drive habilitadas para o projeto.

Credenciais de Conta de Serviço (Service Account) baixadas como um arquivo JSON. Esta conta de serviço precisará de permissões para:

Ler e escrever nas planilhas Google Sheets que você usará.

Ler e escrever na pasta do Google Drive onde os documentos serão armazenados.

Planilha Google Sheets e Pasta no Google Drive:

URLs da planilha e da aba "Usuários" e "Cronograma".

ID da pasta no Google Drive para onde os arquivos serão enviados.

Compartilhe sua planilha e a pasta do Google Drive com o e-mail da sua Conta de Serviço (geralmente algo como nome-da-conta@seu-projeto-id.iam.gserviceaccount.com) concedendo permissões de editor.

Configuração do Ambiente Local
Siga estes passos para configurar e rodar o projeto em sua máquina local:

Clone o Repositório:

git clone [https://github.com/SEU_USUARIO/SEU_PROJETO_PPR.git](https://github.com/SEU_USUARIO/SEU_PROJETO_PPR.git)
cd SEU_PROJETO_PPR

Crie um Ambiente Virtual (Recomendado):

python -m venv venv
# No Windows
venv\Scripts\activate
# No macOS/Linux
source venv/bin/activate

Instale as Dependências:

pip install -r requirements.txt

Configure os Segredos do Streamlit para Desenvolvimento Local:

Crie uma pasta .streamlit na raiz do seu projeto, se ela não existir.

Dentro da pasta .streamlit, crie um arquivo chamado secrets.toml.

Abra o arquivo JSON da sua conta de serviço do Google que você baixou do GCP.

Copie o conteúdo do arquivo JSON e cole-o no secrets.toml sob uma chave chamada gcp_service_account, formatando como um dicionário TOML. Exemplo de secrets.toml:

[gcp_service_account]
type = "service_account"
project_id = "seu-id-de-projeto-aqui"
private_key_id = "seu-id-de-chave-privada-aqui"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA_EM_VARIAS_LINHAS_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "seu-email-de-cliente@seu-id-de-projeto-aqui.iam.gserviceaccount.com"
client_id = "seu-id-de-cliente-aqui"
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "[https://www.googleapis.com/robot/v1/metadata/x509/seu-email-de-cliente%40seu-id-de-projeto-aqui.iam.gserviceaccount.com](https://www.googleapis.com/robot/v1/metadata/x509/seu-email-de-cliente%40seu-id-de-projeto-aqui.iam.gserviceaccount.com)"
# Adicione 'universe_domain = "googleapis.com"' se estiver presente no seu JSON original

Observação: A private_key no TOML precisa ter os \n literais para representar as quebras de linha da chave original.

Atualize as Constantes no Código (se necessário):

Verifique os arquivos .py (especialmente auth.py, app.py, EntregaX.py e utils/google_sheets.py) para constantes como SPREADSHEET_URL, USERS_SHEET, WORKSHEET_NAME e GOOGLE_DRIVE_FOLDER_ID. Certifique-se de que elas correspondem às suas URLs e IDs.

Executando a Aplicação Localmente
Com o ambiente virtual ativado e as dependências instaladas, execute o seguinte comando na raiz do projeto:

streamlit run app.py

A aplicação deverá abrir automaticamente no seu navegador web.

Configuração para Deploy (Ex: Streamlit Community Cloud)
Repositório GitHub:

Certifique-se de que seu projeto (com a estrutura de pastas correta e o arquivo requirements.txt) está no GitHub.

O arquivo .gitignore deve impedir o envio de segredos locais (como service_account.json ou .streamlit/secrets.toml).

Segredos no Streamlit Cloud:

Na plataforma de deploy do Streamlit (ex: Streamlit Community Cloud), acesse as configurações de segredos do seu aplicativo.

Adicione um segredo chamado gcp_service_account.

O valor deste segredo deve ser o conteúdo completo do seu arquivo JSON da conta de serviço, colado diretamente como texto. A plataforma Streamlit irá analisar este JSON.

Visão Geral do Desenvolvimento
A aplicação é estruturada em torno de alguns componentes chave:

app.py (Página Principal / Dashboard):

Verifica se o usuário está logado usando st.session_state.

Se logado, carrega e exibe os dados do cronograma da planilha "Cronograma", filtrados pelo e-mail do usuário.

Aplica filtros avançados sobre os dados exibidos.

Apresenta cada meta como um "card" com suas respectivas entregas.

Fornece botões para navegar para as páginas de edição de cada entrega (pages/EntregaX.py).

Utiliza @st.cache_data para otimizar o carregamento de dados da planilha.

pages/auth.py (Autenticação):

Gerencia o fluxo de login e cadastro de novos usuários.

Interage com a planilha "Usuários" para verificar credenciais e adicionar novos registros.

Armazena o status de login e informações do usuário (email, tipo_usuario) em st.session_state.

pages/EntregaX.py (Páginas de Entrega):

São páginas dedicadas para cada uma das 6 entregas.

Recebem o índice da linha selecionada em app.py via st.session_state.selected_row_index.

Exibem informações da meta e da entrega específica.

Permitem ao usuário editar o campo de avaliação da entrega (ex: "1º Avaliação").

Permitem o upload de um documento para uma pasta configurada no Google Drive. O link do arquivo é salvo na coluna correspondente da entrega (ex: "Doc1") na planilha "Cronograma".

Exibem uma pré-visualização do documento do Drive, se um link válido existir.

Utilizam @st.cache_resource para o cliente Google (gspread e Drive) para otimizar conexões.

utils/google_sheets.py (Módulo de Interação com Google Sheets):

Abstrai a lógica de conexão e manipulação de dados com a API do Google Sheets.

Contém funções para ler dados em DataFrames, adicionar linhas, atualizar células, etc.

Utiliza st.secrets através da função get_gspread_client() para autenticação segura.

Gerenciamento de Estado (st.session_state):

Amplamente utilizado para manter o estado de login do usuário, informações do usuário logado e para passar dados entre páginas (como o selected_row_index).

Gerenciamento de Credenciais (st.secrets):

As credenciais da conta de serviço do Google são gerenciadas de forma segura através do sistema de segredos do Streamlit, tanto para desenvolvimento local (secrets.toml) quanto para deploy.

Como Contribuir
Contribuições são bem-vindas! Se você tem sugestões para melhorar esta aplicação, sinta-se à vontade para:

Fazer um "Fork" do repositório.

Criar uma nova "Branch" (git checkout -b feature/sua-feature).

Fazer suas alterações.

Fazer o "Commit" das suas alterações (git commit -m 'Adiciona nova feature').

Fazer o "Push" para a Branch (git push origin feature/sua-feature).

Abrir um "Pull Request".

Licença
Este projeto é distribuído sob a licença MIT. Veja o arquivo LICENSE para mais detalhes (você precisaria criar um arquivo LICENSE se quiser especificar uma).
