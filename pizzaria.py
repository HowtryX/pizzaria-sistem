import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF

# --- FUNÇÃO PARA GERAR COMANDA ---
def gerar_comanda_pdf(c_nome, total, obs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="COMANDA DE PEDIDO", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"Cliente: {c_nome}", ln=True)
    pdf.cell(200, 10, txt=f"Total: R$ {total:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Obs: {obs}", ln=True)
    
    caminho = "comanda.pdf"
    pdf.output(caminho)
    return caminho

# --- CONFIGURAÇÃO E PERSISTÊNCIA ---
st.set_page_config(page_title="Pizzaria Pro", layout="wide")

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r') as f: return json.load(f)
        except: return padrao
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, 'w') as f: json.dump(dados, f, indent=4)

# Inicialização com carga de arquivos
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
                st.download_button("🖨️ BAIXAR E IMPRIMIR COMANDA", f, "comanda.pdf", "application/pdf")
            st.success("Pedido registrado!")

# --- (O resto do seu código permanece o mesmo para as outras abas) ---
# --- TELA 2: CARDÁPIO ---
elif aba == "Cardápio":
    st.header("Gerenciar Cardápio")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Pizzas")
        df_p = pd.DataFrame(list(st.session_state.pizzas.items()), columns=["Sabor", "Preço"])
        edited_p = st.data_editor(df_p, use_container_width=True)
        with st.expander("➕ Adicionar Pizza"):
            n_p = st.text_input("Nome", key="np_n"); v_p = st.number_input("Preço", key="np_v")
            if st.button("Salvar Pizza"): st.session_state.pizzas[n_p] = v_p; salvar_dados('pizzas.json', st.session_state.pizzas); st.rerun()
                
    with c2:
        st.subheader("Bebidas")
        df_b = pd.DataFrame(list(st.session_state.bebidas.items()), columns=["Bebida", "Preço"])
        edited_b = st.data_editor(df_b, use_container_width=True)
        with st.expander("➕ Adicionar Bebida"):
            n_b = st.text_input("Nome", key="nb_n"); v_b = st.number_input("Preço", key="nb_v")
            if st.button("Salvar Bebida"): st.session_state.bebidas[n_b] = v_b; salvar_dados('bebidas.json', st.session_state.bebidas); st.rerun()
                
    with c3:
        st.subheader("Bordas")
        df_bor = pd.DataFrame(list(st.session_state.bordas.items()), columns=["Borda", "Preço"])
        edited_bor = st.data_editor(df_bor, use_container_width=True)
        with st.expander("➕ Adicionar Borda"):
            n_bor = st.text_input("Nome", key="bor_n"); v_bor = st.number_input("Preço", key="bor_v")
            if st.button("Salvar Borda"): st.session_state.bordas[n_bor] = v_bor; salvar_dados('bordas.json', st.session_state.bordas); st.rerun()
                
        if st.button("💾 Salvar Alterações Gerais"):
            st.session_state.pizzas = dict(zip(edited_p["Sabor"], edited_p["Preço"]))
            st.session_state.bebidas = dict(zip(edited_b["Bebida"], edited_b["Preço"]))
            st.session_state.bordas = dict(zip(edited_bor["Borda"], edited_bor["Preço"]))
            salvar_dados('pizzas.json', st.session_state.pizzas); salvar_dados('bebidas.json', st.session_state.bebidas); salvar_dados('bordas.json', st.session_state.bordas); st.rerun()
            
# --- TELA 3: PROMOÇÕES ---
elif aba == "Promoções":
    st.header("🎁 Promoções Ativas")
    with st.expander("➕ Nova Promoção"):
        todos = {**st.session_state.pizzas, **st.session_state.bebidas}
        prod = st.selectbox("Produto:", list(todos.keys()), key="p_prod")
        val = st.number_input("Desconto (R$):", min_value=0.0, key="p_val")
        if st.button("Adicionar"): st.session_state.promocoes.append({"produto": prod, "desconto": val}); salvar_dados('promocoes.json', st.session_state.promocoes); st.rerun()
    for i, p in enumerate(st.session_state.promocoes):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.warning(f"**{p['produto']}** - Desconto: R$ {p['desconto']:.2f}")
        if c2.button("✏️", key=f"e_{i}"): st.session_state[f"ed_{i}"] = True
        if c3.button("🗑️", key=f"d_{i}"): st.session_state.promocoes.pop(i); salvar_dados('promocoes.json', st.session_state.promocoes); st.rerun()
        if st.session_state.get(f"ed_{i}"):
            nv = st.number_input("Novo valor:", value=p['desconto'], key=f"n_{i}")
            if st.button("Confirmar", key=f"c_{i}"): st.session_state.promocoes[i]['desconto'] = nv; salvar_dados('promocoes.json', st.session_state.promocoes); st.session_state[f"ed_{i}"] = False; st.rerun()

# --- TELA 4: CLIENTES ---
elif aba == "Clientes":
    with st.form("cad"):
        n = st.text_input("Nome"); t = st.text_input("Telefone"); e = st.text_area("Endereço")
        if st.form_submit_button("Cadastrar"): st.session_state.clientes.append({"nome": n, "telefone": t, "endereco": e}); salvar_dados('clientes.json', st.session_state.clientes); st.rerun()
            st.table(pd.DataFrame(st.session_state.clientes))

# --- TELA 5: RELATÓRIO ---
elif aba == "Relatório":
st.table(pd.DataFrame(st.session_state.vendas))













