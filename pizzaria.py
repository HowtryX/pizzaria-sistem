import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF
import base64

# --- FUNÇÕES DE SEGURANÇA PARA DADOS ---
def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f: return json.load(f)
        except: return padrao
    return padrao

def salvar_dados(arquivo, dados):
    # Salva em arquivo temporário antes de substituir para evitar corrupção
    temp_file = arquivo + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f: 
        json.dump(dados, f, indent=4, ensure_ascii=False)
    os.replace(temp_file, arquivo)

# --- FUNÇÃO PARA GERAR COMANDA ---
def gerar_comanda_pdf(c_nome, lista_itens, bebs_dict, total, obs):
    pdf = FPDF(unit='mm', format=(72, 200)) 
    pdf.add_page()
    pdf.set_margins(5, 5, 5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(62, 7, txt="Imperio Rita", ln=True, align='C')
    
    pdf.set_font("Arial", size=9)
    pdf.cell(62, 5, txt=f"Data: {datetime.now().strftime('%d/%m %H:%M')}", ln=True)
    pdf.cell(62, 5, txt=f"Cliente: {c_nome}", ln=True)
    pdf.ln(2)
    
    for i, item in enumerate(lista_itens):
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(62, 5, txt=f"{i+1}. {item['s1']} + {item['s2']}", ln=True)
        pdf.set_font("Arial", size=9)
        pdf.cell(62, 5, txt=f"Borda: {item['borda']} | R$ {item['preco']:.2f}", ln=True)
    
    pdf.ln(2)
    if bebs_dict:
        pdf.cell(62, 5, txt=f"Bebidas: {', '.join(bebs_dict)}", ln=True)
    
    pdf.cell(62, 5, txt=f"Obs: {obs}", ln=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(62, 8, txt=f"TOTAL: R$ {total:.2f}", ln=True, align='R')
    
    caminho = "comanda_termica.pdf"
    pdf.output(caminho)
    return caminho

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="👑Imperio Rita🍕", layout="wide")

# Inicialização com carga de arquivos (Mantém estado persistente)
if 'carrinho' not in st.session_state: st.session_state.carrinho = []
st.session_state.clientes = carregar_dados('clientes.json', [])
st.session_state.pizzas = carregar_dados('pizzas.json', {"Mussarela": 40.0})
st.session_state.bebidas = carregar_dados('bebidas.json', {"Coca-Cola": 10.0})
st.session_state.bordas = carregar_dados('bordas.json', {"Sem Borda": 0.0, "Catupiry": 10.0})
st.session_state.promocoes = carregar_dados('promocoes.json', [])
st.session_state.vendas = carregar_dados('vendas.json', [])

# --- NAVEGAÇÃO ---
aba = st.sidebar.radio("Navegação:", ["PDV - Pedidos", "Cardápio", "Promoções", "Clientes", "Relatório"])

# --- TELA 1: PDV ---
# --- TELA 1: PDV ---
if aba == "PDV - Pedidos":
    st.header("🛒 Terminal de Vendas")
    nome_busca = st.text_input("🔍 Buscar cliente:")
    resultados = [c for c in st.session_state.clientes if nome_busca.lower() in c.get('nome', '').lower()]
    
    if nome_busca and resultados:
        c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x['nome'])
        
        # Aplicar Promoção
        if st.session_state.promocoes:
            with st.expander("🎁 Aplicar Promoção (Combo)"):
                p_sel = st.selectbox("Escolha o combo:", st.session_state.promocoes, format_func=lambda x: x.get('nome', 'Sem Nome'))
                if st.button("Aplicar Promoção"):
                    for _ in range(p_sel.get('qtd_pizzas', 1)):
                        st.session_state.carrinho.append({
                            "s1": p_sel['itens'].get('s1', 'Mussarela'), 
                            "s2": p_sel['itens'].get('s2', 'Nenhum'), 
                            "borda": p_sel['itens'].get('borda', 'Sem Borda'), 
                            "preco": p_sel.get('preco_promocional', 0.0) / p_sel.get('qtd_pizzas', 1),
                            "entrega_gratis": p_sel.get('entrega_inclusa', False)
                        })
                    st.rerun()

        # Carrinho
        if st.session_state.carrinho:
            st.write("### 🛒 Carrinho")
            total_pizzas = sum(item.get('preco', 0) for item in st.session_state.carrinho)
            entrega_gratis = any(item.get('entrega_gratis', False) for item in st.session_state.carrinho)
            taxa_entrega = st.number_input("Taxa de Entrega (R$):", value=0.0 if entrega_gratis else 8.0)
            st.subheader(f"💰 Total: R$ {total_pizzas + taxa_entrega:.2f}")
            
            if st.button("✅ Finalizar"):
                nova_venda = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Cliente": c_sel['nome'], "Itens": st.session_state.carrinho, "Total": total_pizzas + taxa_entrega}
                st.session_state.vendas.append(nova_venda)
                salvar_dados('vendas.json', st.session_state.vendas)
                st.session_state.ultimo_pdf = gerar_comanda_pdf(c_sel['nome'], st.session_state.carrinho, [], total_pizzas + taxa_entrega, "")
                st.rerun()

            if 'ultimo_pdf' in st.session_state:
                with open(st.session_state.ultimo_pdf, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="padding: 10px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">🖨️ IMPRIMIR COMANDA</a>', unsafe_allow_html=True)
                if st.button("🔄 INICIAR NOVO PEDIDO"):
                    st.session_state.carrinho = []
                    del st.session_state.ultimo_pdf
                    st.rerun()

# --- TELA: CARDÁPIO ---
elif aba == "Cardápio":
    st.header("⚙️ Gestão de Preços")
    df_p = pd.DataFrame(list(st.session_state.pizzas.items()), columns=["Sabor", "Preço"])
    edited_p = st.data_editor(df_p, num_rows="dynamic")
    
    if st.button("💾 Salvar Preços"):
        st.session_state.pizzas = dict(zip(edited_p["Sabor"], edited_p["Preço"]))
        salvar_dados('pizzas.json', st.session_state.pizzas)
        st.success("Alterações salvas!")
        st.rerun()

# --- TELA: CLIENTES ---
elif aba == "Clientes":
    with st.form("cad"):
        n = st.text_input("Nome"); t = st.text_input("Telefone"); e = st.text_area("Endereço")
        if st.form_submit_button("Cadastrar"):
            st.session_state.clientes.append({"nome": n, "telefone": t, "endereco": e})
            salvar_dados('clientes.json', st.session_state.clientes)
            st.rerun()
    st.table(pd.DataFrame(st.session_state.clientes))

# --- TELA 3: PROMOÇÕES ---
# --- TELA 3: PROMOÇÕES ---
elif aba == "Promoções":
    st.header("🎁 Criar Promoção")
    with st.expander("➕ Nova Promoção"):
        nome = st.text_input("Nome")
        qtd = st.number_input("Qtd Pizzas", min_value=1, value=1)
        s1 = st.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
        preco = st.number_input("Preço Promocional", min_value=0.0)
        ent = st.checkbox("Entrega Grátis?")
        if st.button("Salvar Promoção"):
            st.session_state.promocoes.append({"nome": nome, "qtd_pizzas": qtd, "itens": {"s1": s1, "s2": "Nenhum", "borda": "Sem Borda"}, "preco_promocional": preco, "entrega_inclusa": ent})
            salvar_dados('promocoes.json', st.session_state.promocoes)
            st.rerun()
    
    for i, p in enumerate(st.session_state.promocoes):
        with st.container(border=True):
            st.write(f"**{p.get('nome')}** - R$ {p.get('preco_promocional')}")
            if st.button("🗑️ Remover", key=f"del_{i}"):
                st.session_state.promocoes.pop(i)
                salvar_dados('promocoes.json', st.session_state.promocoes)
                st.rerun()

    # Exibição das promoções existentes
    st.subheader("Promoções Ativas")
    for i, p in enumerate(st.session_state.promocoes):
        # AQUI ESTÁ A PROTEÇÃO: usamos .get() para não dar KeyError
        nome = p.get('nome', 'Promoção Sem Nome')
        qtd = p.get('qtd_pizzas', 1)
        itens = p.get('itens', {})
        preco = p.get('preco_promocional', 0.0)
        
        with st.container(border=True):
            col_info, col_del = st.columns([5, 1])
            col_info.markdown(f"### {nome}")
            col_info.write(f"🍕 Qtd: {qtd} | Sabor: {itens.get('s1')} + {itens.get('s2')}")
            col_info.subheader(f"💰 Preço: R$ {preco:.2f}")
            
            if col_del.button("🗑️", key=f"del_p_{i}"):
                st.session_state.promocoes.pop(i)
                salvar_dados('promocoes.json', st.session_state.promocoes)
                st.rerun()

# --- TELA: RELATÓRIO ---
elif aba == "Relatório":
    st.header("📊 Vendas")
    st.dataframe(pd.DataFrame(st.session_state.vendas))






