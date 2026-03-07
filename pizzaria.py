import streamlit as st
import pandas as pd
import json
import os

# --- FUNÇÕES DE ARQUIVO ---
def carregar_dados(nome_arquivo):
    if not os.path.exists(nome_arquivo):
        with open(nome_arquivo, 'w') as f:
            json.dump([], f)
    with open(nome_arquivo, 'r') as f:
        return pd.DataFrame(json.load(f))

def salvar_dados(nome_arquivo, df):
    with open(nome_arquivo, 'w') as f:
        json.dump(df.to_dict(orient='records'), f, indent=4)

# --- INTERFACE ---
st.set_page_config(page_title="Pizzaria Simples", layout="wide")
menu = st.sidebar.radio("Navegação", ["PDV", "Cardápio", "Vendas"])

if menu == "PDV":
    st.header("🛒 Pedido")
    # Exemplo de leitura simples
    nome = st.text_input("Cliente")
    valor = st.number_input("Valor")
    
    if st.button("Salvar Pedido"):
        vendas = carregar_dados("vendas.json")
        nova_venda = pd.DataFrame([{"Cliente": nome, "Valor": valor}])
        salvar_dados("vendas.json", pd.concat([vendas, nova_venda]))
        st.success("Pedido salvo!")

elif menu == "Cardápio":
    st.header("📋 Cardápio")
    df_cardapio = carregar_dados("cardapio.json")
    novo_df = st.data_editor(df_cardapio)
    if st.button("Salvar Cardápio"):
        salvar_dados("cardapio.json", novo_df)

elif menu == "Vendas":
    st.header("📊 Relatório")
    st.table(carregar_dados("vendas.json"))
