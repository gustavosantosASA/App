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
            st.stop() # Impede a continuação se a autorização falhar
    else:
        st.error("Credenciais da Conta de Serviço GCP (gcp_service_account) não encontradas nos Segredos do Streamlit.")
        st.stop() # Impede a continuação se as credenciais não estiverem configuradas

def get_google_sheet_by_url(url):
    """Conecta ao Google Sheets usando a URL e retorna a planilha (objeto Spreadsheet)"""
    client = get_gspread_client()
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
        # A mensagem de erro/aviso já foi dada por get_worksheet
        return None # Retorna None para indicar falha no carregamento

    try:
        data = worksheet.get_all_values()
        if not data:
            st.info(f"A aba '{worksheet_name}' na planilha {spreadsheet_url} parece estar vazia.")
            return pd.DataFrame() # Retorna DataFrame vazio se não houver dados
        
        headers = data[0]
        rows = data[1:]
        # Validação para evitar erro se não houver linhas de dados após o cabeçalho
        if not rows:
             return pd.DataFrame(columns=headers) # Retorna DataFrame com colunas mas sem linhas
        return pd.DataFrame(rows, columns=headers)
    except Exception as e:
        st.error(f"Erro ao converter a aba '{worksheet_name}' para DataFrame: {e}")
        return None


def write_dataframe_to_sheet(url, worksheet_name, dataframe):
    """Escreve um DataFrame em uma aba específica, substituindo o conteúdo existente."""
    worksheet = get_worksheet(url, worksheet_name)
    if worksheet:
        try:
            worksheet.clear() # Limpa a planilha existente
            
            headers = dataframe.columns.tolist()
            worksheet.update([headers] + dataframe.values.tolist()) # Mais eficiente para escrita em lote
            st.success(f"DataFrame escrito com sucesso na aba '{worksheet_name}'.")
            return True
        except Exception as e:
            st.error(f"Erro ao escrever DataFrame na aba '{worksheet_name}': {e}")
            return False
    return False

def append_row_to_sheet(url, worksheet_name, row_data):
    """Adiciona uma nova linha (lista de valores) ao final de uma aba."""
    worksheet = get_worksheet(url, worksheet_name)
    if worksheet:
        try:
            worksheet.append_row(row_data)
            # st.success(f"Linha adicionada com sucesso à aba '{worksheet_name}'.") # Pode ser verboso demais
            return True
        except Exception as e:
            st.error(f"Erro ao adicionar linha na aba '{worksheet_name}': {e}")
            return False
    return False

def update_row_in_sheet(url, worksheet_name, row_index_gspread, new_values_list):
    """
    Atualiza uma linha específica na planilha.
    row_index_gspread é 1-based (primeira linha da planilha é 1).
    new_values_list é uma lista de valores para a linha.
    """
    worksheet = get_worksheet(url, worksheet_name)
    if worksheet:
        try:
            # Cria uma lista de células para atualizar em lote
            cell_list_to_update = []
            for col, value in enumerate(new_values_list, start=1):
                cell = gspread.Cell(row=row_index_gspread, col=col, value=value)
                cell_list_to_update.append(cell)
            
            if cell_list_to_update:
                worksheet.update_cells(cell_list_to_update)
                # st.success(f"Linha {row_index_gspread} atualizada com sucesso na aba '{worksheet_name}'.")
                return True
            else:
                st.warning("Nenhum valor fornecido para atualizar a linha.")
                return False
        except Exception as e:
            st.error(f"Erro ao atualizar a linha {row_index_gspread} na aba '{worksheet_name}': {e}")
            return False
    return False

def update_1st_aval_column(url, worksheet_name, row_identifier_value, key_column_name, new_value):
    """
    Atualiza a coluna '1º Avaliação' de uma linha específica, identificada por um valor
    em uma coluna chave.

    :param url: URL da planilha Google Sheets.
    :param worksheet_name: Nome da aba da planilha.
    :param row_identifier_value: Valor na coluna chave que identifica a linha.
    :param key_column_name: Nome da coluna chave (ex: 'Descrição Meta', 'ID').
    :param new_value: Novo valor para a coluna '1º Avaliação'.
    """
    worksheet = get_worksheet(url, worksheet_name)
    if worksheet:
        try:
            data = worksheet.get_all_records() # Retorna lista de dicionários
            if not data:
                st.warning(f"Nenhum dado encontrado na aba '{worksheet_name}' para procurar por '{row_identifier_value}'.")
                return False

            header_list = list(data[0].keys()) # Pega os cabeçalhos da primeira linha de dados (dict keys)
            
            if key_column_name not in header_list:
                st.error(f"Coluna chave '{key_column_name}' não encontrada nos cabeçalhos da planilha: {header_list}")
                return False
            if '1º Avaliação' not in header_list:
                st.error(f"Coluna '1º Avaliação' não encontrada nos cabeçalhos da planilha: {header_list}")
                return False

            target_col_index_gspread = header_list.index('1º Avaliação') + 1 # +1 para ser 1-based

            found = False
            for i, row_dict in enumerate(data, start=2): # start=2 porque get_all_records ignora cabeçalho, e gspread é 1-based para linhas
                if str(row_dict.get(key_column_name)) == str(row_identifier_value):
                    worksheet.update_cell(i, target_col_index_gspread, new_value)
                    st.info(f"Coluna '1º Avaliação' atualizada para '{new_value}' na linha {i} (identificador '{row_identifier_value}').")
                    found = True
                    break # Assume que o identificador é único
            
            if not found:
                st.warning(f"Identificador '{row_identifier_value}' (valor) na coluna '{key_column_name}' não encontrado na aba '{worksheet_name}'.")
                return False
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar '1º Avaliação' para o identificador '{row_identifier_value}': {e}")
            return False
    else:
        # Mensagem de erro já dada por get_worksheet
        return False