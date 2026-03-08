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
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return padrao
    return padrao

def salvar_dados(arquivo, dados):
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
    pdf.cell(62, 5, txt=f"Obs: {obs}", ln=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(62, 8, txt=f"TOTAL: R$ {total:.2f}", ln=True, align='R')
    
    caminho = "comanda_termica.pdf"
    pdf.output(caminho)
    return caminho

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="👑Imperio Rita🍕", layout="wide")

if 'carrinho' not in st.session_state: st.session_state.carrinho = []
if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados('clientes.json', [])
if 'pizzas' not in st.session_state: st.session_state.pizzas = carregar_dados('pizzas.json', {"Mussarela": 40.0})
if 'bebidas' not in st.session_state: st.session_state.bebidas = carregar_dados('bebidas.json', {"Coca-Cola": 10.0})
if 'bordas' not in st.session_state: st.session_state.bordas = carregar_dados('bordas.json', {"Sem Borda": 0.0, "Catupiry": 10.0})
if 'promocoes' not in st.session_state: st.session_state.promocoes = carregar_dados('promocoes.json', [])
if 'vendas' not in st.session_state: st.session_state.vendas = carregar_dados('vendas.json', [])

# --- NAVEGAÇÃO ---
aba = st.sidebar.radio("Navegação:", ["PDV - Pedidos", "Cardápio", "Promoções", "Clientes", "Relatório"])

# --- TELA: PDV ---
if aba == "PDV - Pedidos":
    st.header("🛒 Terminal de Vendas")
    nome_busca = st.text_input("🔍 Buscar cliente:")
    resultados = [c for c in st.session_state.clientes if nome_busca.lower() in c.get('nome', '').lower()]
    c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x.get('nome', 'Sem Nome')) if resultados else None

    if not resultados and nome_busca:
        st.warning("⚠️ Cliente não encontrado.")
    
    if c_sel:
        st.info(f"👤 Cliente: {c_sel.get('nome')} | 📍 {c_sel.get('endereco', 'N/A')}")
        tab_promo, tab_manual = st.tabs(["🎁 Combos/Promoções", "🍕 Seleção Manual"])

        with tab_promo:
            if st.session_state.promocoes:
                p_sel = st.selectbox("Combo:", st.session_state.promocoes, format_func=lambda x: f"{x.get('nome')} - R$ {x.get('preco_promocional', 0):.2f}")
                if st.button("🚀 Aplicar Combo"):
                    qtd = p_sel.get('qtd_pizzas', 1)
                    preco_unit = p_sel.get('preco_promocional', 0) / qtd
                    for _ in range(qtd):
                        st.session_state.carrinho.append({
                            "s1": p_sel.get('itens', {}).get('s1'), "s2": p_sel.get('itens', {}).get('s2'),
                            "borda": p_sel.get('itens', {}).get('borda'), "preco": preco_unit, "entrega_gratis": p_sel.get('entrega_inclusa')
                        })
                    st.rerun()

        with tab_manual:
            c1, c2 = st.columns(2)
            s1_m = c1.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
            s2_m = c2.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()))
            borda_m = c1.selectbox("Borda:", list(st.session_state.bordas.keys()))
            p1 = st.session_state.pizzas.get(s1_m, 0)
            p2 = st.session_state.pizzas.get(s2_m, 0) if s2_m != "Nenhum" else p1
            total_m = ((p1 + p2) / 2) + st.session_state.bordas.get(borda_m, 0)
            
            if st.button("🍕 Adicionar Pizza"):
                st.session_state.carrinho.append({"s1": s1_m, "s2": s2_m, "borda": borda_m, "preco": total_m})
                st.rerun()

    st.write("---")
    st.write("### 🛒 Carrinho")

    if 'ultimo_pdf' in st.session_state:
        st.success("✅ Venda finalizada!")
        with open(st.session_state.ultimo_pdf, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank"><button style="width:100%; background-color:#28a745; color:white; padding:10px; border-radius:5px;">🖨️ IMPRIMIR COMANDA</button></a>', unsafe_allow_html=True)
        if st.button("🔄 Novo Pedido"):
            del st.session_state.ultimo_pdf
            st.rerun()
    elif st.session_state.carrinho:
        for i, item in enumerate(st.session_state.carrinho):
            col_n, col_p, col_b = st.columns([3, 1, 1])
            col_n.write(f"{item['s1']} + {item['s2']}")
            col_p.write(f"R$ {item['preco']:.2f}")
            if col_b.button("🗑️", key=f"del_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()
        
        taxa = st.number_input("Taxa de Entrega:", value=8.0)
        total = sum(i['preco'] for i in st.session_state.carrinho) + taxa
        st.subheader(f"Total: R$ {total:.2f}")
        if st.button("✅ FINALIZAR"):
            st.session_state.vendas.append({"data": datetime.now().strftime("%d/%m/%Y"), "total": total})
            salvar_dados('vendas.json', st.session_state.vendas)
            st.session_state.ultimo_pdf = gerar_comanda_pdf(c_sel['nome'] if c_sel else "Balcão", st.session_state.carrinho, {}, total, "")
            st.session_state.carrinho = []
            st.rerun()
    else:
        st.info("Carrinho vazio.")

# --- TELA: CARDÁPIO ---
elif aba == "Cardápio":
    st.header("⚙️ Gestão de Cardápio")
    tab_p, tab_b, tab_be = st.tabs(["🍕 Pizzas", "🧀 Bordas", "🥤 Bebidas"])

    def gerenciar(chave, arquivo, nome_col):
        df = pd.DataFrame(list(st.session_state[chave].items()), columns=[nome_col, "Preço"])
        editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button(f"💾 Salvar {chave}"):
            st.session_state[chave] = {row[nome_col]: row["Preço"] for _, row in editado.iterrows() if row[nome_col]}
            salvar_dados(arquivo, st.session_state[chave])
            st.rerun()

    with tab_p: gerenciar("pizzas", "pizzas.json", "Sabor")
    with tab_b: gerenciar("bordas", "bordas.json", "Tipo")
    with tab_be: gerenciar("bebidas", "bebidas.json", "Bebida")

# --- TELA: CLIENTES ---
elif aba == "Clientes":
    st.header("👥 Gestão de Clientes")
    df_c = pd.DataFrame(st.session_state.clientes)
    editado_c = st.data_editor(df_c, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Clientes"):
        st.session_state.clientes = editado_c.to_dict('records')
        salvar_dados('clientes.json', st.session_state.clientes)
        st.rerun()

# --- TELA: PROMOÇÕES ---
elif aba == "Promoções":
    st.header("🎁 Promoções")
    with st.expander("➕ Nova Promoção"):
        nome = st.text_input("Nome")
        qtd = st.number_input("Pizzas", min_value=1)
        preco = st.number_input("Preço Total", min_value=0.0)
        if st.button("Salvar Promoção"):
            st.session_state.promocoes.append({"nome": nome, "qtd_pizzas": qtd, "preco_promocional": preco, "itens": {}})
            salvar_dados('promocoes.json', st.session_state.promocoes)
            st.rerun()

# --- TELA: RELATÓRIO ---
elif aba == "Relatório":
    st.header("📊 Vendas")
    st.dataframe(pd.DataFrame(st.session_state.vendas))
