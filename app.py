import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe # Lembre-se de ajustar este arquivo!

# --- Configurações Iniciais ---
st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="Florestal | Cronograma PPR",
    page_icon="📅"
)

# --- Constantes ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=0" # Note: GID is for "Usuários" sheet, not "Cronograma" as in EntregaX files
WORKSHEET_NAME = "Cronograma" #

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
        .delivery-card { /* Estilo não diretamente usado no código HTML fornecido, mas pode ser útil */
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            height: 160px; /* Ajustado no HTML para 180px */
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
        st.switch_page("pages/auth.py") #
    st.stop()

# Inicializa variáveis de sessão se não existirem (redundante se o login sempre as define)
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
            st.cache_data.clear() # Limpa o cache para forçar o recarregamento
            st.rerun()

# --- Carregamento de Dados ---
@st.cache_data(ttl=300) # Cache por 5 minutos
def load_data():
    try:
        # Esta função read_sheet_to_dataframe PRECISA ser ajustada em utils/google_sheets.py
        # para usar st.secrets também!
        df = read_sheet_to_dataframe(SPREADSHEET_URL, WORKSHEET_NAME) #
        if df is None or df.empty:
            st.warning(f"A planilha '{WORKSHEET_NAME}' está vazia ou não pôde ser carregada!") #
            return pd.DataFrame() # Retorna DataFrame vazio para evitar erros subsequentes
            
        # Filtra por e-mail do usuário logado
        if "email" in st.session_state:
            user_email = str(st.session_state.email).strip().lower()
            
            # Verifica as possíveis colunas de email (maiúsculas/minúsculas)
            email_column = None
            if 'E-mail' in df.columns: #
                email_column = 'E-mail'
            elif 'e-mail' in df.columns: #
                email_column = 'e-mail'
            
            if email_column:
                df = df[df[email_column].astype(str).str.lower() == user_email] #
            else:
                st.error("Coluna de e-mail ('E-mail' ou 'e-mail') não encontrada na planilha 'Cronograma'. Não é possível filtrar por usuário.") #
                # Decide se retorna todos os dados ou nenhum
                # return pd.DataFrame() # Opção: não mostrar nada se a coluna de email não existe
                # return df # Opção: mostrar tudo (pode expor dados) - CUIDADO
        else:
            st.warning("E-mail do usuário não encontrado na sessão. Exibindo todos os dados permitidos (se houver).")
            # Decide o que fazer se não houver email na sessão
            # return pd.DataFrame()

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha 'Cronograma': {str(e)}") #
        return pd.DataFrame() # Retorna DataFrame vazio em caso de erro

df_cronograma = load_data()

if df_cronograma is not None and not df_cronograma.empty:
    # --- Filtros Dinâmicos ---
    with st.expander("🔍 Filtros Avançados", expanded=True):
        with st.container():
            st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
            
            def get_filter_options(column, base_df):
                if column not in base_df.columns:
                    st.error(f"Coluna de filtro '{column}' não encontrada na planilha.") #
                    return ["N/A"]
                try:
                    options = base_df[column].unique()
                    return ["Todos"] + sorted(filter(None, set(str(x) for x in options)))
                except KeyError: # Segurança adicional
                    st.error(f"Erro ao acessar a coluna '{column}' para filtros.") #
                    return ["N/A"]

            col1, col2, col3 = st.columns(3)
            selections = {}
            
            # DataFrame base para os filtros em cascata
            df_for_filters = df_cronograma.copy()

            with col1:
                selections['Referência'] = st.selectbox(
                    "Referência",
                    options=get_filter_options('Referência', df_for_filters), #
                    index=0
                )
                
                temp_df_ref = df_for_filters[df_for_filters['Referência'] == selections['Referência']] if selections['Referência'] != "Todos" else df_for_filters
                selections['Setor'] = st.selectbox(
                    "Setor",
                    options=get_filter_options('Setor', temp_df_ref), #
                    index=0
                )

            with col2:
                temp_df_setor = temp_df_ref[temp_df_ref['Setor'] == selections['Setor']] if selections['Setor'] != "Todos" else temp_df_ref
                selections['Responsável'] = st.selectbox(
                    "Responsável",
                    options=get_filter_options('Responsável', temp_df_setor), #
                    index=0
                )
                
                temp_df_resp = temp_df_setor[temp_df_setor['Responsável'] == selections['Responsável']] if selections['Responsável'] != "Todos" else temp_df_setor
                selections['Descrição Meta'] = st.selectbox(
                    "Descrição Meta",
                    options=get_filter_options('Descrição Meta', temp_df_resp), #
                    index=0
                )

            with col3:
                temp_df_meta = temp_df_resp[temp_df_resp['Descrição Meta'] == selections['Descrição Meta']] if selections['Descrição Meta'] != "Todos" else temp_df_resp
                selections['Responsável Área'] = st.selectbox(
                    "Responsável Área",
                    options=get_filter_options('Responsável Área', temp_df_meta), #
                    index=0
                )
                
                # O filtro de E-mail já foi aplicado no load_data, mas pode ser útil para visualização se o admin quiser ver todos.
                # No entanto, para manter a lógica de filtro por usuário logado, este filtro pode ser redundante ou confuso aqui.
                # Se a intenção é permitir que um admin veja outros emails, a lógica do load_data precisa ser ajustada.
                # Por ora, manterei como estava, mas com a observação.
                temp_df_area = temp_df_meta[temp_df_meta['Responsável Área'] == selections['Responsável Área']] if selections['Responsável Área'] != "Todos" else temp_df_meta
                email_col_display = 'E-mail' if 'E-mail' in temp_df_area.columns else 'e-mail' if 'e-mail' in temp_df_area.columns else None
                if email_col_display:
                    selections[email_col_display] = st.selectbox(
                        "E-mail (Filtro Adicional)",
                        options=get_filter_options(email_col_display, temp_df_area), #
                        index=0
                    )
                else:
                    st.text("Coluna de E-mail não disponível para filtro adicional.")
            
            st.markdown("</div>", unsafe_allow_html=True)

    # --- Aplicação de Filtros ---
    filtered_df = df_cronograma.copy()
    for col, val in selections.items():
        if val != "Todos" and col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col].astype(str) == str(val)] # Adicionado astype(str) para robustez
    
    # --- Exibição de Resultados ---
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='header-style'>📊 Resultados: {len(filtered_df)} registros encontrados</div>", unsafe_allow_html=True) #

    if not filtered_df.empty:
        for index, row in filtered_df.iterrows():
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                
                # Simplificando colunas para melhor responsividade, original tinha 7
                cols_header = st.columns([4, 2]) # Ajuste conforme necessidade
                with cols_header[0]:
                    st.markdown(f"<div class='subheader-style'>📑 {row.get('Descrição Meta', 'Meta não descrita')}</div>", unsafe_allow_html=True) #
                
                # Informações da Meta
                st.markdown(f"""
                    <div class='status-box'>
                        <p><strong>Referência:</strong> {row.get('Referência', 'N/A')}</p>
                        <p><strong>Setor:</strong> {row.get('Setor', 'N/A')}</p>
                        <p><strong>Responsável:</strong> {row.get('Responsável', 'N/A')}</p>
                        <p><strong>Responsável Área:</strong> {row.get('Responsável Área', 'N/A')}</p>
                        <p><strong>E-mail:</strong> {row.get('E-mail', row.get('e-mail', 'N/A'))}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---") # Divisor para entregas
                st.markdown("<p style='font-weight: bold;'>Entregas:</p>", unsafe_allow_html=True)

                entregas_cols = st.columns(6) # Uma coluna por entrega
                
                entregas_info = [
                    ('1º Entrega', '1º Avaliação', 'Validação 1º Entrega', "pages/Entrega1.py"), #
                    ('2º Entrega', '2º Avaliação', 'Validação 2º Entrega', "pages/Entrega2.py"), #
                    ('3º Entrega', '3º Avaliação', 'Validação 3º Entrega', "pages/Entrega3.py"), #
                    ('4º Entrega', '4º Avaliação', 'Validação 4º Entrega', "pages/Entrega4.py"), #
                    ('5º Entrega', '5º Avaliação', 'Validação 5º Entrega', "pages/Entrega5.py"), #
                    ('6º Entrega', '6º Avaliação', 'Validação 6º Entrega', "pages/Entrega6.py")  #
                ]
                
                for i, (entrega_col_name, avaliacao_col_name, validacao_col_name, page_link) in enumerate(entregas_info):
                    with entregas_cols[i]:
                        st.markdown(f"""
                            <div style="
                                            border: 1px solid #ccc;
                                            border-radius: 10px;
                                            padding: 10px; /* Reduzido padding */
                                            margin-bottom: 10px;
                                            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                                            height: 200px; /* Aumentado para acomodar botão */
                                            display: flex;
                                            flex-direction: column;
                                            justify-content: space-between;
                                            font-size: 0.9em; /* Fonte menor */
                                            overflow: auto;
                                        ">
                                            <p style="margin: 0; font-weight:bold;">{entrega_col_name.split('º')[0]}ª Entrega:</p>
                                            <p style="margin: 0;">Data: {row.get(entrega_col_name, 'N/A')}</p>
                                            <p style="margin: 0;">Avaliação: {row.get(avaliacao_col_name, 'N/A')}</p>
                                            <p style="margin: 0;">Status: {row.get(validacao_col_name, 'N/A')}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                        
                        if st.button(f"✏️ {entrega_col_name.split('º')[0]}ª", key=f"editar_{i+1}_entrega_{index}_{page_link}"): #
                            st.session_state.selected_row_index = index
                            st.switch_page(page_link)
                
                st.markdown("</div>", unsafe_allow_html=True) # Fecha o card
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    else:
        st.warning("Nenhum registro encontrado com os filtros selecionados ou para o seu usuário!") #
elif df_cronograma is None:
    st.error("Falha ao carregar os dados do cronograma. Verifique a console para mais detalhes e as configurações da planilha.")
else: # df_cronograma está vazio após o load_data (já filtrado por email)
    st.info("Nenhuma meta encontrada para o seu usuário ou com os filtros aplicados.")