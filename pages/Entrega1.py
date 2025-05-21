import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe, update_cell_in_sheet # Funções do seu módulo utils
from googleapiclient.discovery import build # Para Google Drive
from googleapiclient.http import MediaIoBaseUpload # Para Google Drive
from oauth2client.service_account import ServiceAccountCredentials # Para Google Drive
import io
import re

# --- Constantes Específicas da Entrega ---
ENTREGA_NUM = 1
AVALIACAO_COL_NAME = f'{ENTREGA_NUM}º Avaliação'
DOC_COL_NAME = f'Doc{ENTREGA_NUM}'
PAGE_TITLE = f"📝 Gerenciar {ENTREGA_NUM}ª Entrega"

# --- Constantes Globais (podem vir de um config ou serem repetidas) ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=761491838" # URL base da planilha
WORKSHEET_CRONOGRAMA_NAME = "Cronograma"
WORKSHEET_METAS_NAME = "Metas" # Nome da nova aba com detalhes das metas
GOOGLE_DRIVE_FOLDER_ID = '1g-pnfUQV70C7cs5UjWtnRHkfIAYT959t' # SEU ID DA PASTA NO DRIVE AQUI
KEY_COLUMN_METAS = "Descrição Meta" # Coluna chave para ligar Cronograma e Metas

# --- Estilos CSS para a Página de Entrega ---
st.markdown("""
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F0F2F5; }
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 3rem; padding-right: 3rem; }
        
        .page-header { 
            font-size: 2rem; font-weight: 700; color: #004D40; margin-bottom: 0.5rem; 
            /* border-bottom: 2px solid #E0E0E0; padding-bottom: 0.5rem; */
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
        .meta-detail { margin-left: 10px; border-left: 2px solid #004D40; padding-left: 10px; margin-top: 5px;}

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

# --- Carregamento de Dados da Linha Selecionada (Cronograma e Metas) ---
@st.cache_data(ttl=300) # Cache para os dados das planilhas
def load_sheet_data(sheet_url, worksheet_name_cronograma, worksheet_name_metas):
    df_cronograma = read_sheet_to_dataframe(sheet_url, worksheet_name_cronograma)
    df_metas = read_sheet_to_dataframe(sheet_url, worksheet_name_metas)
    return df_cronograma, df_metas

df_all_cronograma, df_all_metas = load_sheet_data(SPREADSHEET_URL, WORKSHEET_CRONOGRAMA_NAME, WORKSHEET_METAS_NAME)

if df_all_cronograma is None or df_all_cronograma.empty:
    st.error("Não foi possível carregar os dados da aba 'Cronograma'. Verifique as configurações.")
    st.stop()
# Não paramos se df_all_metas for None, apenas avisamos e continuamos sem os detalhes da meta.
if df_all_metas is None:
    st.warning(f"Não foi possível carregar os dados da aba '{WORKSHEET_METAS_NAME}'. Detalhes adicionais da meta podem não ser exibidos.")
    df_all_metas = pd.DataFrame() # Cria um DataFrame vazio para evitar erros posteriores

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
    if st.button("⬅️ Voltar ao Painel", key=f"back_to_app_entrega{ENTREGA_NUM}"): # Chave única para o botão
        st.switch_page("app.py")
    st.markdown("</div>", unsafe_allow_html=True)


# --- Seção de Informações da Meta (Cronograma + Detalhes da Aba Metas) ---
with st.container():
    st.markdown("<div class='content-section'>", unsafe_allow_html=True)
    st.markdown("<h3>🎯 Informações da Meta</h3>", unsafe_allow_html=True)
    
    # Informações da Aba Cronograma
    st.markdown(f"""
        <div class='meta-info'>
            <p><strong>Descrição da Meta (Cronograma):</strong> {row_data_cronograma.get(KEY_COLUMN_METAS, 'N/A')}</p>
            <p><strong>Referência:</strong> {row_data_cronograma.get('Referência', 'N/A')}</p>
            <p><strong>Setor:</strong> {row_data_cronograma.get('Setor', 'N/A')}</p>
            <p><strong>Responsável (Cronograma):</strong> {row_data_cronograma.get('Responsável', 'N/A')}</p>
        </div>
    """, unsafe_allow_html=True)

    # Buscar e exibir informações da Aba Metas
    descricao_meta_selecionada = row_data_cronograma.get(KEY_COLUMN_METAS)
    if descricao_meta_selecionada and not df_all_metas.empty and KEY_COLUMN_METAS in df_all_metas.columns:
        # Garante que a comparação seja feita com strings e lide com NaNs
        meta_details_row = df_all_metas[df_all_metas[KEY_COLUMN_METAS].astype(str).str.strip() == str(descricao_meta_selecionada).strip()]
        if not meta_details_row.empty:
            meta_detail = meta_details_row.iloc[0]
            st.markdown("<h4 style='color: #004D40; font-size: 1.1rem; margin-top: 1rem; margin-bottom: 0.5rem;'>Detalhes Adicionais da Meta (da aba 'Metas'):</h4>", unsafe_allow_html=True)
            # Adapte os nomes das colunas conforme sua aba 'Metas'
            st.markdown(f"""
                <div class='meta-info meta-detail'>
                    <p><strong>Peso da Meta:</strong> {meta_detail.get('Peso da Meta', 'N/A')}</p>
                    <p><strong>Indicador:</strong> {meta_detail.get('Indicador', 'N/A')}</p>
                    <p><strong>Tipo de Meta:</strong> {meta_detail.get('Tipo de Meta', 'N/A')}</p>
                    <p><strong>Observações da Meta:</strong> {meta_detail.get('Observações da Meta', 'N/A')}</p>
                    {f"<p><strong>Unidade de Medida:</strong> {meta_detail.get('Unidade de Medida', 'N/A')}</p>" if 'Unidade de Medida' in meta_detail else ''}
                    {f"<p><strong>Fonte de Dados:</strong> {meta_detail.get('Fonte de Dados', 'N/A')}</p>" if 'Fonte de Dados' in meta_detail else ''}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"Nenhum detalhe adicional encontrado na aba '{WORKSHEET_METAS_NAME}' para a meta: '{descricao_meta_selecionada}'.")
    elif not df_all_metas.empty and KEY_COLUMN_METAS not in df_all_metas.columns:
         st.warning(f"A coluna chave '{KEY_COLUMN_METAS}' não foi encontrada na aba '{WORKSHEET_METAS_NAME}'. Não é possível buscar detalhes adicionais.")


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
                st.cache_data.clear() # Limpa o cache para forçar o recarregamento dos dados da planilha
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
                    st.cache_data.clear() # Limpa o cache para forçar o recarregamento dos dados da planilha
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
