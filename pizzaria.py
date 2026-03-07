import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Conexão com o Google Sheets
def conectar_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Aqui o arquivo credenciais.json deve estar na mesma pasta no GitHub
    creds = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', scope)
    client = gspread.authorize(creds)
    return client.open("NomeDaSuaPlanilha")

sheet = conectar_sheets()

def ler_aba(nome):
    return pd.DataFrame(sheet.worksheet(nome).get_all_records())

def salvar_venda(data, cliente, total, obs):
    aba = sheet.worksheet("Vendas")
    aba.append_row([data, cliente, total, obs])

# Interface
st.title("🍕 Pizzaria Pro Online")
menu = st.sidebar.radio("Navegação", ["PDV", "Relatório"])

if menu == "PDV":
    st.subheader("Registrar Pedido")
    nome = st.text_input("Nome do Cliente")
    total = st.number_input("Valor (R$)", value=50.0)
    obs = st.text_area("Observações")
    
    if st.button("Finalizar"):
        salvar_venda(datetime.now().strftime("%d/%m %H:%M"), nome, total, obs)
        st.success("Pedido enviado para a nuvem!")

elif menu == "Relatório":
    st.table(ler_aba("Vendas"))
