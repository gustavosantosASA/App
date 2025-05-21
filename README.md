# Sistema de Gerenciamento de Cronograma PPR

Aplicação web desenvolvida com Streamlit para visualização, edição e acompanhamento de metas e entregas de um cronograma de Programa de Participação nos Resultados (PPR). A aplicação integra-se com Google Sheets para armazenamento de dados e Google Drive para o upload de documentos comprobatórios.

## Funcionalidades Principais

* **Autenticação de Usuários:** Sistema de login e cadastro para acesso seguro.
* **Visualização de Metas:** Exibição do cronograma de metas e suas respectivas entregas, filtrado pelo e-mail do usuário logado.
* **Filtros Avançados:** Permite filtrar as metas por Referência, Setor, Responsável, Descrição da Meta e Responsável da Área.
* **Edição de Entregas:** Usuários podem editar os campos de avaliação de cada entrega.
* **Upload de Documentos:** Funcionalidade para anexar documentos (PDF, DOCX, XLSX, etc.) diretamente para uma pasta específica no Google Drive, associando o link à entrega correspondente na planilha.
* **Pré-visualização de Documentos:** Exibição de uma pré-visualização de documentos do Google Drive diretamente na interface da aplicação.
* **Persistência de Dados:** Utiliza Google Sheets como banco de dados para informações de usuários, metas e avaliações.

## Estrutura do Projeto

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


## Tecnologias Utilizadas

* **Python 3.x**
* **Streamlit:** Framework principal para a construção da interface web.
* **Pandas:** Para manipulação e análise de dados.
* **gspread:** Para interagir com a API do Google Sheets.
* **oauth2client:** Para autenticação com as APIs do Google (usando conta de serviço).
* **google-api-python-client:** Para interagir com a API do Google Drive.
* **Google Sheets:** Utilizado como banco de dados da aplicação.
* **Google Drive:** Utilizado para armazenamento de arquivos anexados.

## Pré-requisitos

Antes de começar, garanta que você tenha o seguinte instalado e configurado:

1.  **Python:** Versão 3.7 ou superior.
2.  **Git:** Para clonar o repositório.
3.  **Conta Google Cloud Platform (GCP):**
    * Um projeto criado no GCP.
    * API do Google Sheets e API do Google Drive habilitadas para o projeto.
    * Credenciais de Conta de Serviço (Service Account) baixadas como um arquivo JSON. Esta conta de serviço precisará de permissões para:
        * Ler e escrever nas planilhas Google Sheets que você usará.
        * Ler e escrever na pasta do Google Drive onde os documentos serão armazenados.
4.  **Planilha Google Sheets e Pasta no Google Drive:**
    * URLs da planilha e da aba "Usuários" e "Cronograma".
    * ID da pasta no Google Drive para onde os arquivos serão enviados.
    * Compartilhe sua planilha e a pasta do Google Drive com o e-mail da sua Conta de Serviço (geralmente algo como `nome-da-conta@seu-projeto-id.iam.gserviceaccount.com`) concedendo permissões de editor.

## Configuração do Ambiente Local

Siga estes passos para configurar e rodar o projeto em sua máquina local:

1.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/SEU_USUARIO/SEU_PROJETO_PPR.git](https://github.com/SEU_USUARIO/SEU_PROJETO_PPR.git)
    cd SEU_PROJETO_PPR
    ```

2.  **Crie um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # No Windows
    venv\Scripts\activate
    # No macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure os Segredos do Streamlit para Desenvolvimento Local:**
    * Crie uma pasta `.streamlit` na raiz do seu projeto, se ela não existir.
    * Dentro da pasta `.streamlit`, crie um arquivo chamado `secrets.toml`.
    * Abra o arquivo JSON da sua conta de serviço do Google que você baixou do GCP.
    * Copie o conteúdo do arquivo JSON e cole-o no `secrets.toml` sob uma chave chamada `gcp_service_account`, formatando como um dicionário TOML. **Exemplo de `secrets.toml`**:

        ```toml
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
        ```
        **Observação:** A `private_key` no TOML precisa ter os `\n` literais para representar as quebras de linha da chave original.

5.  **Atualize as Constantes no Código (se necessário):**
    * Verifique os arquivos `.py` (especialmente `auth.py`, `app.py`, `EntregaX.py` e `utils/google_sheets.py`) para constantes como `SPREADSHEET_URL`, `USERS_SHEET`, `WORKSHEET_NAME` e `GOOGLE_DRIVE_FOLDER_ID`. Certifique-se de que elas correspondem às suas URLs e IDs.

## Executando a Aplicação Localmente

Com o ambiente virtual ativado e as dependências instaladas, execute o seguinte comando na raiz do projeto:

```bash
streamlit run app.py
