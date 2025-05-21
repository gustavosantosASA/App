import streamlit as st
import pandas as pd
from utils.google_sheets import read_sheet_to_dataframe # Lembre-se de que este arquivo foi ajustado para st.secrets

# --- Configurações Iniciais ---
st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="Florestal | Cronograma PPR",
    page_icon="📅" # Você pode usar um emoji ou um link para um ícone .ico/.png
)

# --- Constantes ---
# Ajuste a URL para apontar para a aba "Cronograma" se o GID for diferente
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZpV97NIhd16jAyzMpVE_8VhSs-bSqi4DXmySsx2Kc4/edit#gid=761491838"
WORKSHEET_NAME = "Cronograma"

# --- Estilos CSS Melhorados ---
st.markdown("""
    <style>
        /* Estilo Global */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; /* Fonte mais moderna */
            background-color: #F0F2F5; /* Fundo geral suave */
        }

        /* Remover espaçamento extra no topo introduzido pelo Streamlit em alguns casos */
        .main .block-container {
            padding-top: 2rem; /* Ajuste conforme necessário */
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }

        /* Cabeçalho Principal da Aplicação */
        .app-header {
            font-size: 2.5rem; /* Maior */
            font-weight: 700; /* Mais forte */
            color: #004D40; /* Verde escuro sofisticado */
            margin-bottom: 1.5rem;
            text-align: center; /* Centralizado */
            border-bottom: 2px solid #E0E0E0;
            padding-bottom: 0.5rem;
        }

        /* Informações do Usuário */
        .user-info-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #FFFFFF;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 1.5rem;
        }
        .user-info-item {
            font-size: 0.95rem;
            color: #333333;
        }
        .user-info-item strong {
            color: #004D40;
        }

        /* Botão de Atualizar */
        .user-info-bar .stButton>button {
            background-color: #26A69A; /* Verde secundário */
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background-color 0.3s ease;
        }
        .user-info-bar .stButton>button:hover {
            background-color: #00796B; /* Verde mais escuro no hover */
        }

        /* Caixa de Filtros */
        .filter-box {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            border: 1px solid #E0E0E0; /* Borda sutil */
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .filter-box .stSelectbox label { /* Estilo para labels dos selectbox */
            font-weight: 500;
            color: #004D40;
            font-size: 0.9rem;
        }

        /* Título da Seção de Resultados */
        .results-header {
            font-size: 1.8rem;
            font-weight: 600;
            color: #004D40;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #E0E0E0;
            padding-bottom: 0.3rem;
        }

        /* Card Principal para cada Meta */
        .goal-card {
            background-color: #FFFFFF;
            border-radius: 10px; /* Mais arredondado */
            padding: 1.5rem; /* Mais espaçamento interno */
            margin-bottom: 2rem; /* Mais espaçamento entre cards */
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Sombra mais pronunciada e suave */
            border-top: 4px solid #004D40; /* Destaque superior */
        }

        /* Título da Meta dentro do Card */
        .goal-card-title {
            font-size: 1.5rem; /* Maior */
            font-weight: 600;
            color: #004D40;
            margin-bottom: 1rem;
        }

        /* Caixa de Status/Informações da Meta */
        .status-info-box {
            background-color: #F8F9FA; /* Fundo levemente diferente */
            border-left: 4px solid #26A69A; /* Destaque lateral verde claro */
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
        }
        .status-info-box p {
            margin-bottom: 0.3rem;
            color: #333333;
        }
        .status-info-box p strong {
            color: #004D40;
            margin-right: 5px;
        }

        /* Cards de Entrega */
        .delivery-card {
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem; /* Menor margem se estiverem lado a lado */
            background-color: #FDFDFD;
            height: auto; /* Altura automática para caber o conteúdo */
            min-height: 220px; /* Altura mínima para consistência */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: box-shadow 0.3s ease, transform 0.2s ease;
        }
        .delivery-card:hover {
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
            transform: translateY(-3px);
        }
        .delivery-card-header {
            font-weight: 600;
            color: #004D40;
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }
        .delivery-card p {
            font-size: 0.85rem; /* Texto menor dentro do card de entrega */
            color: #444444;
            margin-bottom: 0.3rem;
            line-height: 1.4;
        }
        .delivery-card .stButton>button { /* Botão de editar entrega */
            background-color: #42A5F5; /* Azul para edição */
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.4rem 0.8rem;
            font-weight: 500;
            font-size: 0.85rem;
            width: 100%; /* Ocupar toda a largura disponível no card */
            margin-top: 0.5rem;
            transition: background-color 0.3s ease;
        }
        .delivery-card .stButton>button:hover {
            background-color: #1E88E5; /* Azul mais escuro */
        }

        /* Divisor Estilizado */
        .custom-divider {
            margin: 2.5rem 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #004D40, transparent);
            opacity: 0.5;
        }

        /* Mensagens de Aviso/Informação */
        .stAlert { /* Estilo para st.warning, st.info, etc. */
            border-radius: 8px;
            font-size: 0.95rem;
        }

        /* Estilo geral para botões (se não especificado) */
        .stButton>button {
            border-radius: 6px;
            font-weight: 500;
        }

    </style>
""", unsafe_allow_html=True)

# --- Verificação de Login ---
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    if st.button("🔐 Fazer login"):
        st.switch_page("pages/auth.py")
    st.stop()

# Inicializa variáveis de sessão (redundante se o login sempre as define, mas seguro)
if 'user_info' not in st.session_state: st.session_state.user_info = {"Login": "Desconhecido"}
if 'email' not in st.session_state: st.session_state.email = "Desconhecido"
if 'tipo_usuario' not in st.session_state: st.session_state.tipo_usuario = "Não definido"

# --- Cabeçalho da Aplicação ---
st.markdown("<div class='app-header'>📅 Cronograma de Metas PPR</div>", unsafe_allow_html=True)

# Barra de informações do usuário
with st.container():
    st.markdown("<div class='user-info-bar'>", unsafe_allow_html=True)
    cols_user_info = st.columns([3,3,3,1.5]) # Ajuste as proporções conforme necessário
    with cols_user_info[0]:
        st.markdown(f"<div class='user-info-item'><strong>👤 Usuário:</strong> {st.session_state.user_info.get('Login', 'N/A')}</div>", unsafe_allow_html=True)
    with cols_user_info[1]:
        st.markdown(f"<div class='user-info-item'><strong>📧 E-mail:</strong> {st.session_state.email}</div>", unsafe_allow_html=True)
    with cols_user_info[2]:
        st.markdown(f"<div class='user-info-item'><strong>🔑 Tipo:</strong> {st.session_state.tipo_usuario}</div>", unsafe_allow_html=True)
    with cols_user_info[3]:
        if st.button("🔄 Atualizar Dados", help="Recarregar dados da planilha"):
            st.cache_data.clear()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# --- Carregamento de Dados ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = read_sheet_to_dataframe(SPREADSHEET_URL, WORKSHEET_NAME)
        if df is None or df.empty:
            # st.warning(f"A planilha '{WORKSHEET_NAME}' está vazia ou não pôde ser carregada!") # Mensagem movida para após o filtro
            return pd.DataFrame()

        if "email" in st.session_state:
            user_email = str(st.session_state.email).strip().lower()
            email_column = None
            if 'E-mail' in df.columns: email_column = 'E-mail'
            elif 'e-mail' in df.columns: email_column = 'e-mail'

            if email_column:
                df_filtered_by_user = df[df[email_column].astype(str).str.lower() == user_email].copy()
                if df_filtered_by_user.empty:
                    st.info(f"Nenhuma meta encontrada para o e-mail: {user_email}")
                return df_filtered_by_user
            else:
                st.error("Coluna de e-mail ('E-mail' ou 'e-mail') não encontrada na planilha 'Cronograma'. Não é possível filtrar por usuário.")
                return pd.DataFrame() # Ou retorna df se admin deve ver tudo
        else:
            st.warning("E-mail do usuário não encontrado na sessão. Não é possível carregar metas.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro crítico ao carregar dados da planilha 'Cronograma': {str(e)}")
        return pd.DataFrame()

df_cronograma = load_data()

if df_cronograma is not None and not df_cronograma.empty:
    # --- Filtros Dinâmicos ---
    with st.expander("🔍 Filtros Avançados", expanded=True):
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        
        def get_filter_options(column, base_df):
            if column not in base_df.columns:
                # st.error(f"Coluna de filtro '{column}' não encontrada.") # Pode ser muito verboso
                return ["Todos"]
            try:
                # Remove NaNs e strings vazias antes de criar opções únicas
                options = base_df[column].dropna().astype(str).str.strip().unique()
                # Filtra novamente para remover strings vazias que podem ter surgido após conversão
                return ["Todos"] + sorted(set(opt for opt in options if opt))
            except KeyError:
                return ["Todos"]

        col1, col2, col3 = st.columns(3)
        selections = {}
        df_for_filters = df_cronograma.copy()

        with col1:
            selections['Referência'] = st.selectbox("Referência", options=get_filter_options('Referência', df_for_filters), index=0)
            temp_df_ref = df_for_filters[df_for_filters['Referência'] == selections['Referência']] if selections['Referência'] != "Todos" else df_for_filters
            selections['Setor'] = st.selectbox("Setor", options=get_filter_options('Setor', temp_df_ref), index=0)
        with col2:
            temp_df_setor = temp_df_ref[temp_df_ref['Setor'] == selections['Setor']] if selections['Setor'] != "Todos" else temp_df_ref
            selections['Responsável'] = st.selectbox("Responsável", options=get_filter_options('Responsável', temp_df_setor), index=0)
            temp_df_resp = temp_df_setor[temp_df_setor['Responsável'] == selections['Responsável']] if selections['Responsável'] != "Todos" else temp_df_setor
            selections['Descrição Meta'] = st.selectbox("Descrição Meta", options=get_filter_options('Descrição Meta', temp_df_resp), index=0)
        with col3:
            temp_df_meta = temp_df_resp[temp_df_resp['Descrição Meta'] == selections['Descrição Meta']] if selections['Descrição Meta'] != "Todos" else temp_df_resp
            selections['Responsável Área'] = st.selectbox("Responsável Área", options=get_filter_options('Responsável Área', temp_df_meta), index=0)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Aplicação de Filtros ---
    filtered_df = df_cronograma.copy()
    for col, val in selections.items():
        if val != "Todos" and col in filtered_df.columns:
            # Garante que a comparação seja feita com strings e lida com NaNs potenciais
            filtered_df = filtered_df[filtered_df[col].astype(str).str.strip() == str(val).strip()]
    
    # --- Exibição de Resultados ---
    st.markdown(f"<div class='results-header'>📊 Resultados: {len(filtered_df)} metas encontradas</div>", unsafe_allow_html=True)

    if not filtered_df.empty:
        for index, row in filtered_df.iterrows():
            with st.container():
                st.markdown("<div class='goal-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='goal-card-title'>📑 {row.get('Descrição Meta', 'Meta não descrita')}</div>", unsafe_allow_html=True)
                
                # Informações da Meta
                st.markdown(f"""
                    <div class='status-info-box'>
                        <p><strong>Referência:</strong> {row.get('Referência', 'N/A')}</p>
                        <p><strong>Setor:</strong> {row.get('Setor', 'N/A')}</p>
                        <p><strong>Responsável:</strong> {row.get('Responsável', 'N/A')}</p>
                        <p><strong>Responsável Área:</strong> {row.get('Responsável Área', 'N/A')}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<h4 style='color: #004D40; font-size: 1.1rem; margin-top: 1rem; margin-bottom: 0.8rem; font-weight: 600;'>Detalhes das Entregas:</h4>", unsafe_allow_html=True)

                entregas_info = [
                    ('1º Entrega', '1º Avaliação', 'Validação 1º Entrega', "pages/Entrega1.py"),
                    ('2º Entrega', '2º Avaliação', 'Validação 2º Entrega', "pages/Entrega2.py"),
                    ('3º Entrega', '3º Avaliação', 'Validação 3º Entrega', "pages/Entrega3.py"),
                    ('4º Entrega', '4º Avaliação', 'Validação 4º Entrega', "pages/Entrega4.py"),
                    ('5º Entrega', '5º Avaliação', 'Validação 5º Entrega', "pages/Entrega5.py"),
                    ('6º Entrega', '6º Avaliação', 'Validação 6º Entrega', "pages/Entrega6.py")
                ]
                
                # Usar colunas para melhor layout das entregas
                num_cols_entregas = 3 # Ajuste para 2 ou 3 para melhor visualização
                delivery_cols = st.columns(num_cols_entregas)
                
                for i, (entrega_col_name, avaliacao_col_name, validacao_col_name, page_link) in enumerate(entregas_info):
                    col_idx = i % num_cols_entregas
                    with delivery_cols[col_idx]:
                        # Usar st.container para cada card de entrega para melhor encapsulamento do botão
                        with st.container(): # Adicionado container para o card
                            st.markdown(f"""
                                <div class='delivery-card'>
                                    <div>
                                        <p class='delivery-card-header'>{entrega_col_name.replace('º', 'ª')}:</p>
                                        <p><strong>Data Prevista:</strong> {row.get(entrega_col_name, 'N/A')}</p>
                                        <p><strong>Avaliação:</strong> {row.get(avaliacao_col_name, 'N/A')}</p>
                                        <p><strong>Status Validação:</strong> {row.get(validacao_col_name, 'N/A')}</p>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            # O botão fica fora do HTML para funcionar corretamente e usar use_container_width
                            if st.button(f"✏️ Gerenciar {entrega_col_name.split('º')[0]}ª Entrega", key=f"editar_{i+1}_entrega_{index}_{page_link.replace('/', '_')}", use_container_width=True):
                                st.session_state.selected_row_index = index
                                st.switch_page(page_link)
                
                st.markdown("</div>", unsafe_allow_html=True) # Fecha o goal-card
                if index != filtered_df.index[-1]: # Adiciona divisor apenas se não for o último card
                    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    elif not df_cronograma.empty: # df_cronograma tem dados, mas filtered_df está vazio
        st.info("Nenhum registro encontrado com os filtros selecionados. Tente refinar sua busca.")
    # Se df_cronograma já estava vazio (filtrado por usuário no load_data), a mensagem já foi dada.

elif df_cronograma is None: # Erro no carregamento
    st.error("Falha crítica ao carregar os dados do cronograma. Verifique as mensagens de erro acima e as configurações da planilha.")
# else: # df_cronograma está vazio (nenhuma meta para o usuário)
    # A mensagem de "Nenhuma meta encontrada para o e-mail" já é dada em load_data
    # Pode-se adicionar uma mensagem mais genérica aqui se desejar.
    # st.info("Não há metas de PPR atribuídas ao seu usuário no momento.") # Removido para evitar duplicidade com load_data

