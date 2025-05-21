import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe
import gspread
from oauth2client.service_account import ServiceAccountCredentials


if "selected_row_index" not in st.session_state:
    st.error("Nenhuma linha selecionada.")
    st.stop()

# URL da planilha e aba
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=761491838"
WORKSHEET_NAME = "Cronograma"

st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

# Verifica se o índice foi passado
if "selected_row_index" not in st.session_state:
    st.error("Nenhuma linha selecionada.")
    st.stop()

df = read_sheet_to_dataframe(SPREADSHEET_URL, WORKSHEET_NAME)
row_index = st.session_state.selected_row_index
row = df.iloc[row_index]

col1, col2 = st.columns([10, 1])
with col2:
    if st.button("⬅️ Voltar", key="voltar_topo"):
       # Remove apenas o índice da linha selecionada
        st.session_state.pop("selected_row_index", None)
        
        # Redireciona usando o método nativo do Streamlit
        st.switch_page("app.py")

with col1:
    st.title("📝 Editar 1º Entrega")

with st.container():
    st.markdown("### 🎯 Informações da Meta")
    st.markdown(f"**Meta:** `{row['Descrição Meta']}`")
    st.markdown(f"1º Entrega")

with st.form("form_avaliacao"):
    new_value = st.text_input("✏️ Editar", value=row['1º Avaliação'])
    submitted = st.form_submit_button("💾 Salvar")

    if submitted:
        # Atualiza valor no Google Sheets
        def update_cell_in_sheet(df, url, worksheet_name, row_index, new_value):
            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials/service_account.json', scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_url(url)
            worksheet = sheet.worksheet(worksheet_name)
            worksheet.update_cell(row_index + 2, df.columns.get_loc('1º Avaliação') + 1, new_value)

        try:
            df.at[row_index, '1º Avaliação'] = new_value
            update_cell_in_sheet(df, SPREADSHEET_URL, WORKSHEET_NAME, row_index, new_value)
            st.success("✅ Dados atualizados com sucesso!")
            
            # Mantém os dados da sessão e redireciona
            st.session_state.selected_row_index = row_index  # Mantém o índice da linha selecionada
            st.experimental_rerun()  # Força atualização da página
            
            
        except Exception as e:
            st.error(f"❌ Erro ao atualizar dados: {e}")


st.markdown("---")
st.markdown("### 📎 Upload de Documento")

uploaded_file = st.file_uploader("Selecione um arquivo para fazer upload (PDF, DOCX, etc.)", type=["pdf", "docx", "doc", "xlsx"])

if uploaded_file is not None:
    import io
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload

    def upload_file_to_drive(file, filename, mimetype):
        scope = ['https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials/service_account.json', scope)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': filename, 'parents': ['1g-pnfUQV70C7cs5UjWtnRHkfIAYT959t']}  # Substitua com o ID da pasta
        media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=mimetype)

        uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        # Torna o arquivo compartilhável
        file_id = uploaded['id']
        service.permissions().create(fileId=file_id, body={"role": "reader", "type": "anyone"}).execute()
        link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        return link

    if st.button("📤 Enviar Documento"):
        filename = uploaded_file.name
        mimetype = uploaded_file.type
        try:
            drive_link = upload_file_to_drive(uploaded_file, filename, mimetype)

            # Atualiza o link na planilha
            def update_doc_link(df, url, worksheet_name, row_index, doc_link):
                scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                creds = ServiceAccountCredentials.from_json_keyfile_name('credentials/service_account.json', scope)
                client = gspread.authorize(creds)
                sheet = client.open_by_url(url)
                worksheet = sheet.worksheet(worksheet_name)
                worksheet.update_cell(row_index + 2, df.columns.get_loc('Doc1') + 1, doc_link)

            df.at[row_index, 'Doc1'] = drive_link
            update_doc_link(df, SPREADSHEET_URL, WORKSHEET_NAME, row_index, drive_link)
            st.success("✅ Documento enviado e link atualizado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao enviar documento: {e}")
            

# 🔍 Pré-visualização do documento, se disponível
if pd.notna(row.get("Doc1")) and "drive.google.com" in row["Doc1"]:
    st.markdown("---")
    st.markdown("### 👁️ Pré-visualização do Documento")

    import re
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", row["Doc1"])
    if match:
        file_id = match.group(1)
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        st.components.v1.html(f"""
            <iframe src="{preview_url}" width="100%" height="480" allow="autoplay"></iframe>
        """, height=500)
    else:
        st.warning("⚠️ Link inválido para visualização.")
