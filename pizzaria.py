import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Configuração da conexão com Google Sheets via Secrets
def conectar_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Carrega as credenciais do segredo configurado no Streamlit Cloud
    creds_dict = st.secrets["gspread"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Abre a planilha pelo nome
    return client.open("NomeDaSuaPlanilha")

# Tenta conectar, se falhar avisa o usuário
try:
    sheet = conectar_sheets()
except Exception as e:
    st.error(f"Erro ao conectar ao Google Sheets: {e}")
    st.stop()

def ler_aba(nome):
    return pd.DataFrame(sheet.worksheet(nome).get_all_records())

def salvar_venda(data, cliente, total, obs):
    aba = sheet.worksheet("Vendas")
    aba.append_row([data, cliente, total, obs])

# --- INTERFACE ---
st.set_page_config(page_title="Pizzaria Cloud", layout="wide")
st.title("🍕 Sistema de Pizzaria")
menu = st.sidebar.radio("Navegação", ["PDV", "Relatório"])

if menu == "PDV":
    st.subheader("Registrar Pedido")
    nome = st.text_input("Nome do Cliente")
    total = st.number_input("Valor (R$)", value=50.0)
    obs = st.text_area("Observações")
    
    if st.button("Finalizar Pedido"):
        salvar_venda(datetime.now().strftime("%d/%m %H:%M"), nome, total, obs)
        st.success("Pedido enviado para o Google Sheets!")

elif menu == "Relatório":
    st.subheader("📊 Vendas")
    df = ler_aba("Vendas")
    st.dataframe(df, use_container_width=True)
