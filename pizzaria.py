import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURAÇÃO E PERSISTÊNCIA ---
st.set_page_config(page_title="Pizzaria Pro", layout="wide")

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r') as f: return json.load(f)
        except: return padrao
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, 'w') as f: json.dump(dados, f)

# --- FUNÇÃO DE IMPRESSÃO ---
def gerar_comanda_pdf(c_nome, total, obs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="COMANDA DE PEDIDO", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"Cliente: {c_nome}", ln=True)
    pdf.cell(200, 10, txt=f"Total: R$ {total:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Obs: {obs}", ln=True)
    caminho = "comanda.pdf"
    pdf.output(caminho)
    return caminho

# Inicialização
if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados('clientes.json', [])
if 'pizzas' not in st.session_state: st.session_state.pizzas = carregar_dados('pizzas.json', {"Mussarela": 40.0})
if 'bebidas' not in st.session_state: st.session_state.bebidas = carregar_dados('bebidas.json', {"Coca-Cola": 10.0})
if 'bordas' not in st.session_state: st.session_state.bordas = carregar_dados('bordas.json', {"Sem Borda": 0.0, "Catupiry": 10.0})
if 'promocoes' not in st.session_state: st.session_state.promocoes = carregar_dados('promocoes.json', [])
if 'vendas' not in st.session_state: st.session_state.vendas = carregar_dados('vendas.json', [])

# --- NAVEGAÇÃO ---
st.sidebar.title("🍕 Menu do App")
aba = st.sidebar.radio("Navegação:", ["PDV - Pedidos", "Cardápio", "Promoções", "Clientes", "Relatório"])

# --- TELA 1: PDV ---
if aba == "PDV - Pedidos":
    st.header("🛒 Terminal de Vendas")
    nome_busca = st.text_input("🔍 Buscar cliente pelo NOME:")
    resultados = [c for c in st.session_state.clientes if nome_busca.lower() in c['nome'].lower()]
    
    if nome_busca and resultados:
        c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x['nome'])
        st.info(f"📍 Endereço: {c_sel.get('endereco', 'Não cadastrado')}")
        
        col1, col2 = st.columns(2)
        with col1:
            s1 = st.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
            s2 = st.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()))
            borda_sel = st.selectbox("Escolha a Borda:", list(st.session_state.bordas.keys()))
            taxa_entrega = st.number_input("Taxa de Entrega (R$):", value=5.0)
        with col2:
            bebs = st.multiselect("Bebidas:", list(st.session_state.bebidas.keys()))
            qtde_bebs = {b: st.number_input(f"Qtd {b}", min_value=1, value=1, key=f"k_{b}") for b in bebs}
            obs = st.text_area("📝 Observações:")

        preco_base = max(st.session_state.pizzas.get(s1, 0), st.session_state.pizzas.get(s2, 0) if s2 != "Nenhum" else 0)
        v_borda = st.session_state.bordas.get(borda_sel, 0)
        preco_bebs = sum([st.session_state.bebidas.get(b, 0) * qtde_bebs[b] for b in bebs])
        desc = sum([p['desconto'] for p in st.session_state.promocoes if p['produto'] in [s1, s2] + bebs])
        
        total = (preco_base + v_borda + preco_bebs + taxa_entrega) - desc
        st.subheader(f"💰 Total: R$ {total:.2f}")

        if st.button("✅ FINALIZAR E IMPRIMIR"):
            nova_venda = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Cliente": c_sel['nome'], "Total": total, "Obs": obs}
            st.session_state.vendas.append(nova_venda)
            salvar_dados('vendas.json', st.session_state.vendas)
            
            caminho_pdf = gerar_comanda_pdf(c_sel['nome'], total, obs)
            with open(caminho_pdf, "rb") as f:
                st.download_button("🖨️ BAIXAR COMANDA PARA IMPRIMIR", f, "comanda.pdf", "application/pdf")
            st.success("Pedido registrado!")

# --- (Mantenha as outras telas de Cardápio, Promoções, etc, abaixo) ---
# [O código das
