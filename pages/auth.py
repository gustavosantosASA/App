import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe, append_row_to_sheet # Funções do seu módulo utils
from datetime import datetime
# Removido gspread e ServiceAccountCredentials daqui, pois a interação com sheets deve ser via utils

# --- Constantes ---
SPREADSHEET_URL_USERS = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=0" # URL específica da aba Usuários
USERS_SHEET_NAME = "Usuários"

# --- Estilos CSS para a Página de Autenticação ---
st.markdown("""
    <style>
        /* Estilo Global da Página */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #F0F2F5; /* Mesmo fundo suave do app.py */
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .auth-container {
            max-width: 450px; /* Largura um pouco menor para forms */
            margin: 3rem auto; /* Mais margem no topo */
            padding: 2.5rem; /* Mais padding interno */
            background-color: #FFFFFF;
            border-radius: 12px; /* Bordas mais arredondadas */
            box-shadow: 0 6px 20px rgba(0,0,0,0.1); /* Sombra mais pronunciada */
            border-top: 5px solid #004D40; /* Destaque superior verde escuro */
        }
        .auth-header {
            font-size: 2rem;
            font-weight: 700;
            color: #004D40;
            text-align: center;
            margin-bottom: 2rem;
        }
        /* Estilo para os botões de rádio */
        .stRadio > label { /* Label do st.radio (ex: "Escolha uma opção:") */
            font-weight: 500;
            color: #004D40;
            text-align: center;
            display: block;
            margin-bottom: 1rem;
        }
        .stRadio > div[role="radiogroup"] { /* Container dos botões de rádio */
            display: flex;
            justify-content: center; /* Centraliza os botões de rádio */
            gap: 1rem; /* Espaço entre os botões de rádio */
            margin-bottom: 1.5rem;
        }
        .stRadio > div[role="radiogroup"] > label { /* Estilo individual de cada opção do rádio */
            padding: 0.5rem 1rem;
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            transition: background-color 0.3s, border-color 0.3s;
        }
        .stRadio > div[role="radiogroup"] > label:hover {
            background-color: #E8F5E9; /* Verde bem claro no hover */
            border-color: #26A69A;
        }
        /* Estilo para inputs e botões dentro do form */
        .auth-container .stTextInput label, .auth-container .stSelectbox label {
            font-weight: 500;
            color: #333; /* Cor mais suave para labels de input */
            font-size: 0.9rem;
        }
        .auth-container .stButton>button {
            background-color: #004D40;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.6rem 1.2rem;
            font-weight: 500;
            width: 100%; /* Botão ocupa largura total */
            margin-top: 1.5rem; /* Espaço acima do botão */
            transition: background-color 0.3s ease;
        }
        .auth-container .stButton>button:hover {
            background-color: #00382e; /* Verde mais escuro no hover */
        }
        .auth-container .stAlert {
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)


# --- Funções de Autenticação ---
def authenticate_user(login_input, senha_input, df_users_auth):
    if df_users_auth is None or df_users_auth.empty:
        st.error("Não foi possível carregar os dados dos usuários para autenticação.")
        return None
    # Garante que a comparação seja feita com strings e lide com NaNs
    user = df_users_auth[
        (df_users_auth['Login'].astype(str).str.strip() == str(login_input).strip()) &
        (df_users_auth['Senha'].astype(str).str.strip() == str(senha_input).strip())
    ]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

# --- Inicialização da sessão ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "df_users" not in st.session_state: # Cache simples dos usuários para evitar releitura constante
    st.session_state.df_users = read_sheet_to_dataframe(SPREADSHEET_URL_USERS, USERS_SHEET_NAME)


# --- Layout da Página ---
st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
st.markdown("<h1 class='auth-header'>🔐 Portal de Acesso</h1>", unsafe_allow_html=True)

df_users_cached = st.session_state.df_users

if not st.session_state["logged_in"]:
    modo = st.radio("Escolha uma opção:", ["Login", "Cadastrar Novo Usuário"], horizontal=True, key="auth_mode_radio")

    if modo == "Login":
        with st.form("form_login"):
            login = st.text_input("Login", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            submitted_login = st.form_submit_button("🔓 Entrar")

            if submitted_login:
                if not login or not senha:
                    st.warning("Por favor, preencha o login e a senha.")
                else:
                    user_info = authenticate_user(login, senha, df_users_cached)
                    if user_info:
                        st.session_state["logged_in"] = True
                        st.session_state["user_info"] = user_info
                        st.session_state["email"] = user_info.get("Email", user_info.get("E-mail")) # Lida com variações de nome de coluna
                        st.session_state["tipo_usuario"] = user_info.get("Tipo de Usuário")
                        st.success(f"Bem-vindo(a), {user_info.get('Login')}!")
                        st.switch_page("app.py") # Redireciona para a página principal
                    else:
                        st.error("❌ Login ou senha inválidos.")
    else:  # Cadastro
        with st.form("form_cadastro"):
            st.markdown("<h2 style='text-align:center; color:#004D40; font-size:1.5rem; margin-bottom:1rem;'>📝 Novo Cadastro</h2>", unsafe_allow_html=True)
            novo_login = st.text_input("Login para acesso", key="reg_login")
            novo_email = st.text_input("Seu E-mail", key="reg_email")
            nova_senha = st.text_input("Crie uma Senha", type="password", key="reg_pass")
            confirm_senha = st.text_input("Confirme a Senha", type="password", key="reg_confirm_pass")
            tipo_usuario_options = ["Avaliador", "Gestor | Avaliador"] # Opções mais simples
            tipo_usuario = st.selectbox("Tipo de Usuário", tipo_usuario_options, key="reg_usertype")
            
            submitted_cadastro = st.form_submit_button("✅ Cadastrar Usuário")

            if submitted_cadastro:
                if not novo_login or not novo_email or not nova_senha or not confirm_senha or not tipo_usuario:
                    st.warning("Por favor, preencha todos os campos do cadastro.")
                elif nova_senha != confirm_senha:
                    st.error("As senhas não coincidem.")
                elif df_users_cached is not None and novo_login in df_users_cached['Login'].astype(str).str.strip().values:
                    st.warning("⚠️ Este login já existe. Tente outro.")
                elif df_users_cached is not None and novo_email in df_users_cached['Email'].astype(str).str.strip().values: # Verifica se o email já existe
                    st.warning("⚠️ Este e-mail já está cadastrado. Tente outro ou faça login.")
                else:
                    data_cadastro = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                    # A ordem das colunas deve corresponder à sua planilha "Usuários"
                    new_user_data = [novo_login, novo_email, nova_senha, tipo_usuario, data_cadastro]
                    
                    if append_row_to_sheet(SPREADSHEET_URL_USERS, USERS_SHEET_NAME, new_user_data):
                        st.success("✅ Usuário cadastrado com sucesso! Você já pode fazer o login.")
                        # Atualiza o cache local de usuários
                        st.session_state.df_users = read_sheet_to_dataframe(SPREADSHEET_URL_USERS, USERS_SHEET_NAME)
                        # Limpar campos do formulário (Streamlit não tem um método direto, o rerun do form ajuda)
                    else:
                        st.error("❌ Ocorreu um erro ao cadastrar o usuário. Tente novamente.")
else:
    # Usuário já logado, teoricamente não deveria estar nesta página, mas pode adicionar um redirecionamento ou mensagem.
    st.info("Você já está logado.")
    if st.button("Ir para o Painel Principal"):
        st.switch_page("app.py")

st.markdown("</div>", unsafe_allow_html=True)
