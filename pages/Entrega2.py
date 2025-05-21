import streamlit as st
import pandas as pd
import io
import re
import sys # Standard library
import os  # Standard library

# --- Adjust sys.path to ensure utils module is found ---
# This assumes the 'pages' directory is directly under the project root,
# and 'utils' is also directly under the project root.
try:
    # Get the absolute path of the directory containing the current script (pages/)
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the project root directory (one level up from pages/)
    project_root = os.path.dirname(current_script_dir)
    # Add the project root to the Python path if it's not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    # __file__ might not be defined in some contexts (e.g., interactive interpreter)
    # For Streamlit page scripts, __file__ should typically be available.
    # If running into issues here in a specific environment, this part might need adjustment.
    pass

# --- Local application imports ---
from utils.google_sheets import read_sheet_to_dataframe, update_cell_in_sheet # Funções do seu módulo utils

# --- Third-party imports for Google APIs ---
from googleapiclient.discovery import build # Para Google Drive
from googleapiclient.http import MediaIoBaseUpload # Para Google Drive
from oauth2client.service_account import ServiceAccountCredentials # Para Google Drive


# --- Constantes Específicas da Entrega ---
ENTREGA_NUM = 2
AVALIACAO_COL_NAME = f'{ENTREGA_NUM}º Avaliação'
DOC_COL_NAME = f'Doc{ENTREGA_NUM}'
PAGE_TITLE = f"📝 Gerenciar {ENTREGA_NUM}ª Entrega"

# --- Constantes Globais (podem vir de um config ou serem repetidas) ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=761491838" # URL base da planilha
WORKSHEET_CRONOGRAMA_NAME = "Cronograma"
# WORKSHEET_METAS_NAME = "Metas" # Removido, pois os dados estão no Cronograma
GOOGLE_DRIVE_FOLDER_ID = '1g-pnfUQV70C7cs5UjWtnRHkfIAYT959t' # SEU ID DA PASTA NO DRIVE AQUI
# KEY_COLUMN_METAS = "Descrição Meta" # Removido, não é mais necessário para cruzar abas

# !!! IMPORTANTE: ATUALIZE ESTA LISTA COM OS NOMES REAIS DAS SUAS COLUNAS AP ATÉ BN !!!
# Estes são placeholders. A ordem e os nomes devem corresponder à sua planilha "Cronograma".
COLUMNS_TO_DISPLAY_FROM_CRONOGRAMA = [
    "U.M.", "Operador", "Meta", "%PPR", "Operador 1",
   "Meta 1", "%PPR 1", "Operador 2", "Meta 2", "%PPR 2",
    "Operador 3", "Meta 3", "%PPR 3", "Operador 4", "Meta 4",
    "%PPR 4", "Operador 5", "Meta 5", "%PPR 5", "Operador 6",
    "Meta 6", "%PPR 6", "Operador 7", "Meta 7", "%PPR 7"
    # Adicione ou remova conforme o número exato de colunas entre AP e BN
]


# --- Estilos CSS para a Página de Entrega ---
st.markdown("""
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F0F2F5; }
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 3rem; padding-right: 3rem; }
        
        .page-header { 
            font-size: 2rem; font-weight: 700; color: #004D40; margin-bottom: 0.5rem; 
        }
        .back-button-col { display: flex; align-items: center; justify-content: flex-end; }
        .back-button-col .stButton>button {
            background-color: #6c757d; /* Cinza para voltar */
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background-color 0.3s ease;
        }
        .back-button-col .stButton>button:hover { background-color: #5a6268; }

        .content-section {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-bottom: 1.5rem;
            border-top: 4px solid #26A69A; 
        }
        .content-section h3 { color: #004D40; margin-top: 0; margin-bottom: 1rem; font-size: 1.3rem; }
        
        .stButton>button.primary-action { background-color: #004D40; color: white; }
        .stButton>button.primary-action:hover { background-color: #00382e; }
        .stButton>button.secondary-action { background-color: #42A5F5; color: white; }
        .stButton>button.secondary-action:hover { background-color: #1E88E5; }

        .preview-container { margin-top: 1rem; }
        .preview-iframe { border: 1px solid #E0E0E0; border-radius: 8px; min-height: 500px; }
        .meta-info p { margin-bottom: 0.3rem; font-size: 0.95rem; }
        .meta-info strong { color: #004D40; }
        /* .meta-detail { margin-left: 10px; border-left: 2px solid #004D40; padding-left: 10px; margin-top: 5px;} */ /* Removido pois não há mais a seção de detalhes da aba Metas */

        .cronograma-extra-info-section {
            background-color: #FFFFFF; /* Fundo branco para o card de detalhes */
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-top: 1rem;
            margin-bottom: 1.5rem;
            border-top: 4px solid #004D40; /* Destaque superior verde escuro */
        }
        .cronograma-extra-info-section h4 {
            color: #004D40;
            font-size: 1.2rem; /* Ajuste no tamanho do título da seção */
            margin-top: 0;
            margin-bottom: 1rem; /* Mais espaço abaixo do título */
        }
        /* Estilo para o DataFrame */
        .cronograma-extra-info-section .stDataFrame {
            width: 100%; /* DataFrame ocupa toda a largura */
        }
        .cronograma-extra-info-section .stDataFrame table {
            font-size: 0.9rem; /* Tamanho da fonte na tabela */
        }
        .cronograma-extra-info-section .stDataFrame th {
            background-color: #E8F5E9; /* Fundo do cabeçalho da tabela */
            color: #004D40; /* Cor do texto do cabeçalho */
            font-weight: 600;
            text-align: left; /* Alinha cabeçalhos à esquerda */
        }
         .meta-info-basic {
            margin-bottom: 10px; 
            padding-bottom:10px; 
            border-bottom: 1px dashed #C8E6C9;
        }

    </style>
""", unsafe_allow_html=True)


# --- Configuração de Credenciais do Google para Drive (usando st.secrets) ---
@st.cache_resource(ttl=3600) # Cacheia por 1 hora
def get_drive_service():
    scope_drive = ['https://www.googleapis.com/auth/drive']
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope_drive)
            service = build('drive', 'v3', credentials=creds)
            return service
        except Exception as e:
            st.error(f"Erro ao autenticar com Google Drive via st.secrets: {e}")
            st.stop()
    else:
        st.error("Credenciais 'gcp_service_account' não encontradas nos Segredos do Streamlit para o Google Drive.")
        st.stop()

drive_service = get_drive_service()

# --- Verificação de Login e Seleção de Linha ---
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    if st.button("🔐 Fazer login"): st.switch_page("pages/auth.py")
    st.stop()

if "selected_row_index" not in st.session_state:
    st.error("Nenhuma meta selecionada. Volte para a página principal e selecione uma meta para gerenciar suas entregas.")
    if st.button("⬅️ Voltar para o Painel"): st.switch_page("app.py")
    st.stop()

# --- Carregamento de Dados da Linha Selecionada (Apenas Cronograma) ---
@st.cache_data(ttl=300) # Cache para os dados da planilha
def load_cronograma_data(sheet_url, worksheet_name_cronograma):
    df_cronograma = read_sheet_to_dataframe(sheet_url, worksheet_name_cronograma)
    return df_cronograma

df_all_cronograma = load_cronograma_data(SPREADSHEET_URL, WORKSHEET_CRONOGRAMA_NAME)

if df_all_cronograma is None or df_all_cronograma.empty:
    st.error("Não foi possível carregar os dados da aba 'Cronograma'. Verifique as configurações.")
    st.stop()

selected_idx = st.session_state.selected_row_index
if selected_idx >= len(df_all_cronograma):
    st.error("O item selecionado não existe mais ou a planilha 'Cronograma' foi alterada. Por favor, volte e selecione novamente.")
    if st.button("⬅️ Voltar para o Painel"): st.switch_page("app.py")
    st.stop()

row_data_cronograma = df_all_cronograma.iloc[selected_idx]

# --- Layout da Página ---
header_cols = st.columns([8,2])
with header_cols[0]:
    st.markdown(f"<div class='page-header'>{PAGE_TITLE}</div>", unsafe_allow_html=True)
with header_cols[1]:
    st.markdown("<div class='back-button-col'>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar ao Painel", key=f"back_to_app_entrega{ENTREGA_NUM}"): 
        st.switch_page("app.py")
    st.markdown("</div>", unsafe_allow_html=True)

# --- SEÇÃO: Exibição de Dados das Colunas AP-BN da Aba Cronograma ---
with st.container():
    st.markdown("<div class='cronograma-extra-info-section'>", unsafe_allow_html=True)
    st.markdown("<h4>Detalhes da Meta (Conforme Aba Cronograma)</h4>", unsafe_allow_html=True) 
    
    # Exibe primeiro as informações básicas da meta (Descrição, Referência, Setor, Responsável)
    st.markdown(f"""
        <div class='meta-info meta-info-basic'>
            <p><strong>Descrição da Meta:</strong> {row_data_cronograma.get('Descrição Meta', 'N/A')}</p>
            <p><strong>Referência:</strong> {row_data_cronograma.get('Referência', 'N/A')}</p>
            <p><strong>Setor:</strong> {row_data_cronograma.get('Setor', 'N/A')}</p>
            <p><strong>Responsável:</strong> {row_data_cronograma.get('Responsável', 'N/A')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Agora exibe as colunas de AP a BN como um DataFrame de uma única linha
    # Filtra as colunas que realmente existem no row_data_cronograma para evitar KeyErrors
    cols_to_show_in_df = [col for col in COLUMNS_TO_DISPLAY_FROM_CRONOGRAMA if col in row_data_cronograma.index]
    
    if not cols_to_show_in_df:
        st.info("Nenhuma das colunas de detalhe da meta (AP-BN) foi encontrada nos dados do cronograma ou a lista de colunas precisa ser atualizada no script.")
    else:
        # Cria um dicionário para os dados da linha única
        single_row_data_dict = {}
        for col_name in cols_to_show_in_df:
            # Usa o nome da coluna original como chave no dicionário
            # O valor é obtido da linha de dados do cronograma
            single_row_data_dict[col_name] = row_data_cronograma.get(col_name, "N/D")
        
        if single_row_data_dict:
            # Cria o DataFrame a partir do dicionário, envolvendo-o em uma lista para criar uma única linha
            details_df_single_row = pd.DataFrame([single_row_data_dict])
            st.dataframe(details_df_single_row, use_container_width=True, hide_index=True)
        else:
            # Este caso é improvável se cols_to_show_in_df não estiver vazio, mas é uma salvaguarda
            st.info("Não há dados para exibir nas colunas AP-BN para esta meta.")
            
    st.markdown("</div>", unsafe_allow_html=True)

# --- Seção de Edição da Avaliação ---
with st.container():
    st.markdown("<div class='content-section'>", unsafe_allow_html=True)
    st.markdown(f"<h3>✏️ Avaliação da {ENTREGA_NUM}ª Entrega</h3>", unsafe_allow_html=True)
    with st.form(f"form_avaliacao_entrega{ENTREGA_NUM}"):
        current_avaliacao = row_data_cronograma.get(AVALIACAO_COL_NAME, '')
        new_avaliacao = st.text_area("Insira sua avaliação ou observações:", value=current_avaliacao, height=100, key=f"text_aval_e{ENTREGA_NUM}")
        submitted_avaliacao = st.form_submit_button(f"💾 Salvar Avaliação da {ENTREGA_NUM}ª Entrega")

        if submitted_avaliacao:
            if update_cell_in_sheet(SPREADSHEET_URL, WORKSHEET_CRONOGRAMA_NAME, df_all_cronograma, selected_idx, AVALIACAO_COL_NAME, new_avaliacao):
                st.success(f"Avaliação da {ENTREGA_NUM}ª Entrega atualizada com sucesso!")
                st.cache_data.clear() 
                st.rerun() 
            else:
                st.error(f"Falha ao atualizar a avaliação da {ENTREGA_NUM}ª Entrega.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- Seção de Upload de Documento ---
with st.container():
    st.markdown("<div class='content-section'>", unsafe_allow_html=True)
    st.markdown(f"<h3>📎 Documento da {ENTREGA_NUM}ª Entrega</h3>", unsafe_allow_html=True)

    def upload_to_drive(file_to_upload, drive_filename, drive_mimetype):
        try:
            file_metadata = {'name': drive_filename, 'parents': [GOOGLE_DRIVE_FOLDER_ID]}
            media = MediaIoBaseUpload(io.BytesIO(file_to_upload.read()), mimetype=drive_mimetype, resumable=True)
            uploaded_file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            
            file_id = uploaded_file_drive.get('id')
            permission = {'type': 'anyone', 'role': 'reader'} 
            drive_service.permissions().create(fileId=file_id, body=permission).execute()
            return uploaded_file_drive.get('webViewLink')
        except Exception as e_drive:
            st.error(f"Erro ao fazer upload para o Google Drive: {e_drive}")
            return None

    uploaded_file_st = st.file_uploader(f"Selecione um arquivo para a {ENTREGA_NUM}ª Entrega (PDF, DOCX, XLSX, etc.)", 
                                        type=["pdf", "docx", "doc", "xlsx", "xls", "txt", "png", "jpg", "jpeg", "ppt", "pptx"], 
                                        key=f"uploader_e{ENTREGA_NUM}")

    if uploaded_file_st is not None:
        if st.button(f"📤 Enviar Documento da {ENTREGA_NUM}ª Entrega", key=f"btn_upload_e{ENTREGA_NUM}"):
            with st.spinner(f"Enviando {uploaded_file_st.name}..."):
                gdrive_link = upload_to_drive(uploaded_file_st, uploaded_file_st.name, uploaded_file_st.type)
            
            if gdrive_link:
                if update_cell_in_sheet(SPREADSHEET_URL, WORKSHEET_CRONOGRAMA_NAME, df_all_cronograma, selected_idx, DOC_COL_NAME, gdrive_link):
                    st.success(f"Documento '{uploaded_file_st.name}' enviado com sucesso! Link atualizado na planilha.")
                    st.markdown(f"**Link do arquivo:** [{gdrive_link}]({gdrive_link})")
                    st.cache_data.clear() 
                    st.rerun()
                else:
                    st.error("Documento enviado para o Drive, mas falha ao atualizar o link na planilha.")
            else:
                st.error("Falha no upload do documento para o Google Drive.")
    
    current_doc_link = row_data_cronograma.get(DOC_COL_NAME)
    if pd.notna(current_doc_link) and "drive.google.com" in str(current_doc_link):
        st.markdown("<div class='preview-container'>", unsafe_allow_html=True)
        st.markdown(f"<h6>Documento Atual: <a href='{current_doc_link}' target='_blank'>{current_doc_link}</a></h6>", unsafe_allow_html=True)
        
        match_id = re.search(r"/d/([a-zA-Z0-9_-]+)", str(current_doc_link))
        if match_id:
            file_id_drive = match_id.group(1)
            preview_url_drive = f"https://drive.google.com/file/d/{file_id_drive}/preview"
            st.components.v1.html(f"""
                <iframe src="{preview_url_drive}" class="preview-iframe" width="100%" height="500" allow="autoplay; encrypted-media" frameborder="0"></iframe>
            """, height=520)
        else:
            st.warning("Não foi possível gerar a pré-visualização. O link do Drive pode ser inválido ou o arquivo não permite incorporação.")
        st.markdown("</div>", unsafe_allow_html=True)
    elif pd.notna(current_doc_link):
        st.markdown(f"<h6>Link do Documento Atual (não é do Google Drive ou formato não reconhecido para preview): <a href='{current_doc_link}' target='_blank'>{current_doc_link}</a></h6>", unsafe_allow_html=True)
    else:
        st.info(f"Nenhum documento associado à {ENTREGA_NUM}ª Entrega ainda.")

    st.markdown("</div>", unsafe_allow_html=True)
