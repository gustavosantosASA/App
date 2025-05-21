import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe # Lembre-se de ajustar este arquivo!
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=0"
USERS_SHEET = "Usuários"

# --- Configuração de Credenciais do Google ---
def get_google_creds():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        try:
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except Exception as e:
            st.error(f"Erro ao carregar credenciais da conta de serviço: {e}")
            st.stop()
    else:
        st.error("Credenciais da Conta de Serviço GCP (gcp_service_account) não encontradas nos Segredos do Streamlit.")
        st.stop()

google_creds = get_google_creds()
gspread_client = gspread.authorize(google_creds)

# --- Funções ---
def append_user_to_sheet(new_user):
    try:
        sheet = gspread_client.open_by_url(SPREADSHEET_URL)
        worksheet = sheet.worksheet(USERS_SHEET)
        worksheet.append_row(new_user)
    except Exception as e:
        st.error(f"Erro ao adicionar usuário na planilha: {e}")
        st.stop()

def authenticate_user(login, senha, df_users):
    user = df_users[(df_users['Login'] == login) & (df_users['Senha'] == senha)]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

# --- Inicialização da sessão ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- Lê dados da planilha ---
# Esta função read_sheet_to_dataframe PRECISA ser ajustada em utils/google_sheets.py
# para usar st.secrets também!
df_users = read_sheet_to_dataframe(SPREADSHEET_URL, USERS_SHEET)
if df_users is None: # Adicionado para tratar falha no carregamento
    st.error("Não foi possível carregar os dados dos usuários. Verifique as configurações da planilha e credenciais.")
    st.stop()


st.title("🔐 Portal de Acesso")

# --- Conteúdo baseado no estado de login ---
if not st.session_state["logged_in"]:
    modo = st.radio("Escolha uma opção:", ["Login", "Cadastrar Novo Usuário"])

    if modo == "Login":
        login = st.text_input("Login")
        senha = st.text_input("Senha", type="password")

        if st.button("🔓 Entrar"):
            user_info = authenticate_user(login, senha, df_users)
            if user_info:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = user_info
                st.session_state["email"] = user_info["Email"]
                st.session_state["tipo_usuario"] = user_info["Tipo de Usuário"]
                st.success(f"Bem-vindo, {user_info['Login']}!")
                st.switch_page("app.py")
            else:
                st.error("❌ Login ou senha inválidos.")

    else:  # Cadastro
        with st.form("form_cadastro"):
            novo_login = st.text_input("Novo Login")
            novo_email = st.text_input("Email")
            nova_senha = st.text_input("Senha", type="password")
            tipo_usuario = st.selectbox("Tipo de Usuário", ["Gestor | Avaliador", "Avaliador"])
            submit = st.form_submit_button("✅ Cadastrar")

            if submit:
                if novo_login in df_users['Login'].values:
                    st.warning("⚠️ Este login já existe.")
                else:
                    data = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                    append_user_to_sheet([novo_login, novo_email, nova_senha, tipo_usuario, data])
                    st.success("✅ Usuário cadastrado com sucesso. Faça login na aba anterior.")
                    # Recarregar dados dos usuários após cadastro
                    st.session_state.df_users = read_sheet_to_dataframe(SPREADSHEET_URL, USERS_SHEET)

else:
    # --- Conteúdo para usuário logado ---
    user_info = st.session_state["user_info"]
    st.success(f"👋 Bem-vindo, {user_info['Login']} ({user_info['Email']})")
    st.write("Tipo de usuário:", user_info["Tipo de Usuário"])

    if st.button("🚪 Sair"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun() # Usar st.rerun() para limpar e recarregar a página de login