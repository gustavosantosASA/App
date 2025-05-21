import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Escopo unificado para todas as operações do gspread neste módulo
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

@st.cache_resource(ttl=300) # Cacheia o cliente gspread por 5 minutos
def get_gspread_client():
    """
    Autoriza e retorna um cliente gspread usando credenciais do st.secrets.
    O cliente é cacheado para otimizar o desempenho.
    """
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
            client = gspread.authorize(creds)
            return client
        except Exception as e:
            st.error(f"Erro ao autorizar o cliente gspread com st.secrets: {e}")
            return None # Retornar None em caso de falha na autorização
    else:
        st.error("Credenciais da Conta de Serviço GCP (gcp_service_account) não encontradas nos Segredos do Streamlit.")
        return None # Retornar None

def get_google_sheet_by_url(url):
    """Conecta ao Google Sheets usando a URL e retorna a planilha (objeto Spreadsheet)"""
    client = get_gspread_client()
    if not client:
        return None # Cliente não autorizado
    try:
        sheet = client.open_by_url(url)
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Planilha não encontrada na URL fornecida: {url}")
        return None
    except Exception as e:
        st.error(f"Erro ao acessar a planilha pela URL ({url}): {e}")
        return None

def get_worksheet(url, worksheet_name):
    """Obtém uma aba específica (objeto Worksheet) da planilha"""
    sheet = get_google_sheet_by_url(url)
    if sheet:
        try:
            worksheet = sheet.worksheet(worksheet_name)
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            st.warning(f"Aba '{worksheet_name}' não encontrada na planilha {url}.")
            return None
        except Exception as e:
            st.error(f"Erro ao obter a aba '{worksheet_name}': {e}")
            return None
    return None

def read_sheet_to_dataframe(spreadsheet_url, worksheet_name):
    """
    Lê uma aba específica de uma planilha do Google Sheets e a retorna como um DataFrame pandas.
    """
    worksheet = get_worksheet(spreadsheet_url, worksheet_name)
    if not worksheet:
        return None # Falha no carregamento, mensagem já dada

    try:
        data = worksheet.get_all_values()
        if not data:
            return pd.DataFrame() 
        
        headers = data[0]
        rows = data[1:]
        
        if not headers: 
             st.warning(f"A aba '{worksheet_name}' em {spreadsheet_url} não contém cabeçalhos.")
             return pd.DataFrame()

        processed_rows = []
        num_headers = len(headers)
        for row in rows:
            # Ensure each row has the same number of elements as headers, padding with None if necessary
            row_len = len(row)
            if row_len < num_headers:
                processed_rows.append(row + [None] * (num_headers - row_len))
            elif row_len > num_headers:
                processed_rows.append(row[:num_headers]) # Truncate if row is too long
            else:
                processed_rows.append(row)
        
        return pd.DataFrame(processed_rows, columns=headers)
    except Exception as e:
        st.error(f"Erro ao converter a aba '{worksheet_name}' para DataFrame: {e}")
        return None


def write_dataframe_to_sheet(url, worksheet_name, dataframe):
    """Escreve um DataFrame em uma aba específica, substituindo o conteúdo existente."""
    worksheet = get_worksheet(url, worksheet_name)
    if worksheet:
        try:
            worksheet.clear() 
            
            headers = dataframe.columns.tolist()
            # worksheet.update([headers] + dataframe.values.tolist()) # gspread v5+
            # For older gspread or to be safe:
            worksheet.update_cells(gspread.utils.fill_gaps(worksheet.range(1,1,len(dataframe.index)+1,len(headers))),[headers] + dataframe.values.tolist())

            return True
        except Exception as e:
            st.error(f"Erro ao escrever DataFrame na aba '{worksheet_name}': {e}")
            return False
    return False

def append_row_to_sheet(url, worksheet_name, row_data_list):
    """Adiciona uma nova linha (lista de valores) ao final de uma aba."""
    worksheet = get_worksheet(url, worksheet_name)
    if worksheet:
        try:
            worksheet.append_row(row_data_list)
            return True
        except Exception as e:
            st.error(f"Erro ao adicionar linha na aba '{worksheet_name}': {e}")
            return False
    return False

def update_cell_in_sheet(url, worksheet_name, df_reference_for_headers, row_index_df, col_name_df, new_value):
    """
    Atualiza uma célula específica na planilha.
    row_index_df é o índice 0-based do DataFrame.
    col_name_df é o nome da coluna no DataFrame.
    df_reference_for_headers é um DataFrame que possui os cabeçalhos corretos para encontrar o índice da coluna.
    """
    worksheet = get_worksheet(url, worksheet_name)
    if not worksheet:
        st.error(f"Não foi possível obter a aba '{worksheet_name}' para atualização.")
        return False

    try:
        # Converte o índice do DataFrame (0-based) para o índice da linha do gspread (1-based, +1 para cabeçalho)
        gspread_row_index = int(row_index_df) + 2 
        
        # Encontra o índice da coluna no gspread (1-based)
        if df_reference_for_headers is None or df_reference_for_headers.columns is None:
            st.error("DataFrame de referência para cabeçalhos é inválido.")
            return False
            
        headers = df_reference_for_headers.columns.tolist()
        if col_name_df not in headers:
            st.error(f"Coluna '{col_name_df}' não encontrada nos cabeçalhos: {headers}")
            return False
        gspread_col_index = headers.index(col_name_df) + 1

        worksheet.update_cell(gspread_row_index, gspread_col_index, str(new_value) if new_value is not None else "") # Convert to string to avoid gspread issues with types
        return True
    except ValueError: 
        st.error(f"Índice da linha inválido: {row_index_df}")
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar célula (linha_gspread:{gspread_row_index}, col_gspread:{gspread_col_index}) na aba '{worksheet_name}': {e}")
        return False
