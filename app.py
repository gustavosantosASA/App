import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe

# --- Configurações Iniciais ---
st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="Florestal | Cronograma PPR",
    page_icon="📅"
)

# --- Constantes ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=0"
WORKSHEET_NAME = "Cronograma"

# --- Estilos CSS ---
st.markdown("""
    <style>
        .header-style {
            font-size: 24px;
            font-weight: bold;
            color: #20643f;
            margin-bottom: 10px;
        }
        .subheader-style {
            font-size: 18px;
            font-weight: 600;
            color: #40b049;
            margin-bottom: 5px;
        }
        .card {
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-box {
            border-left: 3px solid #40b049;
            padding: 10px;
            margin: 5px 0;
        }
        .filter-box {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 3px solid #20643f;
        }
        .stButton>button {
            background-color: #40b049;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #20643f;
        }
        .divider {
            margin: 20px 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #40b049, transparent);
        }
        .delivery-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            height: 160px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
    </style>
""", unsafe_allow_html=True)

# --- Verificação de Login ---
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    if st.button("🔐 Fazer login"):
        st.switch_page("pages/auth.py")
    st.stop()

# Inicializa variáveis de sessão se não existirem
if 'user_info' not in st.session_state:
    st.session_state.user_info = {"Login": "Desconhecido"}
if 'email' not in st.session_state:
    st.session_state.email = "Desconhecido"
if 'tipo_usuario' not in st.session_state:
    st.session_state.tipo_usuario = "Não definido"

# --- Cabeçalho ---
st.markdown("<div class='header-style'>📅 Cronograma PPR</div>", unsafe_allow_html=True)

# Barra de informações do usuário
with st.container():
    cols = st.columns([3, 3, 3, 1])
    with cols[0]:
        st.markdown(f"<div class='subheader-style'>👤 Usuário: {st.session_state.user_info.get('Login', 'Desconhecido')}</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='subheader-style'>📧 E-mail: {st.session_state.email}</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"<div class='subheader-style'>🔑 Tipo: {st.session_state.tipo_usuario}</div>", unsafe_allow_html=True)
    with cols[3]:
        if st.button("🔄 Atualizar", help="Atualizar dados da planilha"):
            st.cache_data.clear()
            st.rerun()

# --- Carregamento de Dados ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = read_sheet_to_dataframe(SPREADSHEET_URL, WORKSHEET_NAME)
        if df.empty:
            st.warning("A planilha está vazia!")
            return None
            
        # Filtra por e-mail do usuário logado
        if "email" in st.session_state:
            user_email = str(st.session_state.email).strip().lower()
            if 'E-mail' in df.columns:
                df = df[df['E-mail'].str.lower() == user_email]
            elif 'e-mail' in df.columns:
                df = df[df['e-mail'].str.lower() == user_email]
            else:
                st.error("Coluna de e-mail não encontrada na planilha.")
                
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

df = load_data()

if df is not None:
    # --- Filtros Dinâmicos ---
    with st.expander("🔍 Filtros Avançados", expanded=True):
        with st.container():
            st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
            
            def get_filter_options(column, base_df):
                try:
                    options = base_df[column].unique()
                    return ["Todos"] + sorted(filter(None, set(str(x) for x in options)))
                except KeyError:
                    st.error(f"Coluna '{column}' não encontrada")
                    return ["N/A"]

            col1, col2, col3 = st.columns(3)
            selections = {}
            
            with col1:
                selections['Referência'] = st.selectbox(
                    "Referência",
                    options=get_filter_options('Referência', df),
                    index=0
                )
                
                temp_df = df[df['Referência'] == selections['Referência']] if selections['Referência'] != "Todos" else df
                selections['Setor'] = st.selectbox(
                    "Setor",
                    options=get_filter_options('Setor', temp_df),
                    index=0
                )

            with col2:
                if selections['Setor'] != "Todos":
                    temp_df = temp_df[temp_df['Setor'] == selections['Setor']]
                
                selections['Responsável'] = st.selectbox(
                    "Responsável",
                    options=get_filter_options('Responsável', temp_df),
                    index=0
                )
                
                if selections['Responsável'] != "Todos":
                    temp_df = temp_df[temp_df['Responsável'] == selections['Responsável']]
                
                selections['Descrição Meta'] = st.selectbox(
                    "Descrição Meta",
                    options=get_filter_options('Descrição Meta', temp_df),
                    index=0
                )

            with col3:
                if selections['Descrição Meta'] != "Todos":
                    temp_df = temp_df[temp_df['Descrição Meta'] == selections['Descrição Meta']]
                
                selections['Responsável Área'] = st.selectbox(
                    "Responsável Área",
                    options=get_filter_options('Responsável Área', temp_df),
                    index=0
                )
                
                if selections['Responsável Área'] != "Todos":
                    temp_df = temp_df[temp_df['Responsável Área'] == selections['Responsável Área']]
                
                selections['E-mail'] = st.selectbox(
                    "E-mail",
                    options=get_filter_options('E-mail', temp_df),
                    index=0
                )
            
            st.markdown("</div>", unsafe_allow_html=True)

    # --- Aplicação de Filtros ---
    filtered_df = df.copy()
    for col, val in selections.items():
        if val != "Todos" and col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col] == val]
    
    # --- Exibição de Resultados ---
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='header-style'>📊 Resultados: {len(filtered_df)} registros encontrados</div>", unsafe_allow_html=True)

    if not filtered_df.empty:
        for index, row in filtered_df.iterrows():
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                
                cols_header = st.columns([3, 1, 1, 1, 1, 1, 1])
                with cols_header[0]:
                    st.markdown(f"<div class='subheader-style'>📑 {row['Descrição Meta']}</div>", unsafe_allow_html=True)
                
                cols_content = st.columns([3, 1, 1, 1, 1, 1, 1])
                
                with cols_content[0]:
                    st.markdown(f"""
                        <div class='status-box'>
                            <p><strong>Referência:</strong> {row['Referência']}</p>
                            <p><strong>Setor:</strong> {row['Setor']}</p>
                            <p><strong>Responsável:</strong> {row['Responsável']}</p>
                            <p><strong>Responsável Área:</strong> {row['Responsável Área']}</p>
                            <p><strong>E-mail:</strong> {row.get('E-mail', row.get('e-mail', 'N/A'))}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                entregas = [
                    ('1º Entrega', '1º Avaliação', 'Validação 1º Entrega', "pages/Entrega1.py"),
                    ('2º Entrega', '2º Avaliação', 'Validação 2º Entrega', "pages/Entrega2.py"),
                    ('3º Entrega', '3º Avaliação', 'Validação 3º Entrega', "pages/Entrega3.py"),
                    ('4º Entrega', '4º Avaliação', 'Validação 4º Entrega', "pages/Entrega4.py"),
                    ('5º Entrega', '5º Avaliação', 'Validação 5º Entrega', "pages/Entrega5.py"),
                    ('6º Entrega', '6º Avaliação', 'Validação 6º Entrega', "pages/Entrega6.py")
                ]
                
                for i, (entrega, avaliacao, validacao, page) in enumerate(entregas, start=1):
                    with cols_content[i]:
                        st.markdown(f"""
                            <div style="
                                            border: 1px solid #ccc;
                                            border-radius: 10px;
                                            padding: 16px;
                                            margin-bottom: 10px;
                                            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                                            height: 180px;
                                            display: flex;
                                            flex-direction: column;
                                            justify-content: space-between;
                                            overflow: auto;  /* Adiciona scroll se necessário */
                                        ">
                                            <p style="margin: 0;"><strong>{entrega.split('º')[0]}º Entrega:</strong> {row[entrega]}</p>
                                            <p style="margin: 0;"><strong>→ </strong> {row[avaliacao]}</p>
                                            <p style="margin: 0;"><strong>Status: </strong> {row[validacao]}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                        
                        if st.button(f"✏️ {entrega.split('º')[0]}º", key=f"editar_{i}_entrega_{index} Entrega"):
                            st.session_state.selected_row_index = index
                            st.switch_page(page)
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    else:
        st.warning("Nenhum registro encontrado com os filtros selecionados!")
