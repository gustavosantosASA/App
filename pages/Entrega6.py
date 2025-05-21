import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe # Lembre-se de ajustar este arquivo!
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re

# --- Constantes Específicas da Entrega ---
ENTREGA_NUM = 6 # Mude para 2, 3, 4, 5, 6 nos respectivos arquivos
AVALIACAO_COL = f'{ENTREGA_NUM}º Avaliação'
DOC_COL = f'Doc{ENTREGA_NUM}'
PAGE_TITLE = f"📝 Editar {ENTREGA_NUM}ª Entrega"

# URL da planilha e aba
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=761491838" # [cite: 1]
WORKSHEET_NAME = "Cronograma" # [cite: 1]
GOOGLE_DRIVE_FOLDER_ID = '1g-pnfUQV70C7cs5UjWtnRHkfIAYT959t' # [cite: 1] ID da pasta no Drive

# --- Configuração de Credenciais do Google ---
@st.cache_resource(ttl=300) # Cache do objeto de credenciais e clientes
def get_google_clients():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            gspread_client = gspread.authorize(creds)
            drive_service = build('drive', 'v3', credentials=creds)
            return gspread_client, drive_service, creds # Retorna creds para uso direto se necessário
        except Exception as e:
            st.error(f"Erro ao carregar credenciais da conta de serviço: {e}")
            st.stop()
    else:
        st.error("Credenciais da Conta de Serviço GCP (gcp_service_account) não encontradas nos Segredos do Streamlit.")
        st.stop()

gspread_client, drive_service, google_creds = get_google_clients()


st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True) # [cite: 1]

if "selected_row_index" not in st.session_state:
    st.error("Nenhuma linha selecionada. Volte para a página principal e selecione uma meta.") # [cite: 1]
    if st.button("⬅️ Voltar para Home"):
        st.switch_page("app.py")
    st.stop()

# É importante recarregar o dataframe aqui para ter os dados mais recentes
# A função read_sheet_to_dataframe PRECISA ser ajustada em utils/google_sheets.py para usar st.secrets!
df = read_sheet_to_dataframe(SPREADSHEET_URL, WORKSHEET_NAME)
if df is None or df.empty:
    st.error("Não foi possível carregar os dados da planilha. Verifique as configurações e credenciais.")
    st.stop()

row_index = st.session_state.selected_row_index

# Validação do índice da linha
if row_index >= len(df):
    st.error("Índice da linha selecionada é inválido. A planilha pode ter sido alterada. Por favor, volte e selecione novamente.")
    if st.button("⬅️ Voltar para Home"):
        st.switch_page("app.py")
    st.stop()
row = df.iloc[row_index] # [cite: 1]


col1, col2 = st.columns([10, 1])
with col2:
    if st.button("⬅️ Voltar", key="voltar_topo"): # [cite: 1]
        st.session_state.pop("selected_row_index", None) # [cite: 1]
        st.switch_page("app.py") # [cite: 1]
with col1:
    st.title(PAGE_TITLE)

with st.container():
    st.markdown("### 🎯 Informações da Meta")
    st.markdown(f"**Meta:** `{row.get('Descrição Meta', 'N/A')}`") # [cite: 1]
    st.markdown(f"{ENTREGA_NUM}ª Entrega")

# --- Formulário de Avaliação ---
def update_cell_in_sheet(sheet_url, sheet_name, df_ref, row_idx, col_name, new_val):
    try:
        sheet = gspread_client.open_by_url(sheet_url)
        worksheet = sheet.worksheet(sheet_name)
        # +2 porque gspread é 1-indexed e temos cabeçalho na planilha
        worksheet.update_cell(row_idx + 2, df_ref.columns.get_loc(col_name) + 1, new_val) # [cite: 1]
    except Exception as e:
        st.error(f"Erro ao atualizar célula na planilha: {e}")
        raise # Propaga o erro para ser tratado no form

with st.form("form_avaliacao"):
    new_value_avaliacao = st.text_input("✏️ Editar Avaliação", value=row.get(AVALIACAO_COL, '')) # [cite: 1]
    submitted_avaliacao = st.form_submit_button("💾 Salvar Avaliação")

    if submitted_avaliacao:
        try:
            update_cell_in_sheet(SPREADSHEET_URL, WORKSHEET_NAME, df, row_index, AVALIACAO_COL, new_value_avaliacao)
            st.success(f"✅ Avaliação da {ENTREGA_NUM}ª Entrega atualizada com sucesso!")
            # Força o recarregamento da página para mostrar o valor atualizado no input
            # e para recarregar 'row' do dataframe que pode ser re-lido.
            st.rerun() 
        except Exception as e:
            # O erro já é mostrado por update_cell_in_sheet, mas podemos adicionar mais contexto se necessário
            st.error(f"❌ Falha ao salvar avaliação: {e}")


st.markdown("---")
st.markdown("### 📎 Upload de Documento")

# --- Upload de Documento ---
def upload_file_to_gdrive(file_obj, filename, mimetype):
    try:
        file_metadata = {'name': filename, 'parents': [GOOGLE_DRIVE_FOLDER_ID]} # [cite: 1]
        media = MediaIoBaseUpload(io.BytesIO(file_obj.read()), mimetype=mimetype, resumable=True) # [cite: 1]
        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute() # [cite: 1]
        
        # Torna o arquivo compartilhável (qualquer um com o link pode ver)
        file_id = uploaded_file.get('id')
        permission = {'type': 'anyone', 'role': 'reader'}
        drive_service.permissions().create(fileId=file_id, body=permission).execute() # [cite: 1]
        
        # Retorna o link de visualização, não o de download direto se não for o objetivo
        return uploaded_file.get('webViewLink') # Ou use o formato de link que preferir
        # return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing" # Formato de link alternativo [cite: 1]
    except Exception as e:
        st.error(f"Erro ao fazer upload do arquivo para o Google Drive: {e}")
        raise

uploaded_file = st.file_uploader(f"Selecione um arquivo para a {ENTREGA_NUM}ª Entrega (PDF, DOCX, etc.)", type=["pdf", "docx", "doc", "xlsx", "txt", "png", "jpg"]) # [cite: 1]

if uploaded_file is not None:
    if st.button(f"📤 Enviar Documento da {ENTREGA_NUM}ª Entrega"):
        filename = uploaded_file.name # [cite: 1]
        mimetype = uploaded_file.type # [cite: 1]
        try:
            drive_link = upload_file_to_gdrive(uploaded_file, filename, mimetype)
            if drive_link:
                update_cell_in_sheet(SPREADSHEET_URL, WORKSHEET_NAME, df, row_index, DOC_COL, drive_link)
                st.success(f"✅ Documento da {ENTREGA_NUM}ª Entrega enviado e link atualizado com sucesso!")
                st.markdown(f"Link do arquivo: [{drive_link}]({drive_link})")
                st.rerun()
        except Exception as e:
            # Erros já são tratados nas funções chamadas
            pass # Apenas para evitar que a página pare completamente, mensagens de erro já foram dadas.
            

# --- Pré-visualização do Documento ---
doc_link_value = row.get(DOC_COL) # [cite: 1]
if pd.notna(doc_link_value) and "drive.google.com" in str(doc_link_value): # [cite: 1]
    st.markdown("---")
    st.markdown("### 👁️ Pré-visualização do Documento")

    match = re.search(r"/d/([a-zA-Z0-9_-]+)", str(doc_link_value)) # [cite: 1]
    if match:
        file_id = match.group(1)
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview" # [cite: 1]
        st.components.v1.html(f""" 
            <p>Visualizando: <a href="{doc_link_value}" target="_blank">{doc_link_value}</a></p>
            <iframe src="{preview_url}" width="100%" height="480" allow="autoplay"></iframe>
        """, height=520) # [cite: 1]
    else:
        st.warning(f"⚠️ Link do Google Drive (`{doc_link_value}`) parece inválido para gerar pré-visualização, mas você pode tentar abri-lo diretamente.") # [cite: 1]
        st.markdown(f"Link direto: [{doc_link_value}]({doc_link_value})")
elif pd.notna(doc_link_value):
    st.markdown("---")
    st.markdown("### 🔗 Link do Documento")
    st.markdown(f"O documento associado a esta entrega pode ser acessado aqui: [{doc_link_value}]({doc_link_value})")