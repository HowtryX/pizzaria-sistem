import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import base64
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="👑Imperio Rita🍕", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def ler_dados(aba):
    """Lê uma aba da planilha e retorna um DataFrame ou vazio se houver erro."""
    try:
        # ttl=0 garante que ele busque o dado mais recente da planilha sempre
        return conn.read(worksheet=aba, ttl=0)
    except Exception:
        return pd.DataFrame()
def salvar_dados_sheets(df, aba):
    try:
        # Remove linhas onde o nome/sabor esteja vazio
        df_limpo = df.dropna(how='all') 
        conn.update(worksheet=aba, data=df_limpo)
        st.cache_data.clear()
        st.success(f"✅ Dados salvos na aba {aba}!")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
# --- INICIALIZAÇÃO E CARGA DE DADOS ---
if 'carrinho' not in st.session_state: st.session_state.carrinho = []

# Carregando os dados das planilhas
df_clientes_raw = ler_dados("clientes")
df_pizzas_raw = ler_dados("pizzas")
df_bebidas_raw = ler_dados("bebidas")
df_bordas_raw = ler_dados("bordas")
df_vendas_raw = ler_dados("vendas")
df_promo_raw = ler_dados("promocoes")

# Convertendo para os formatos que o seu código já utiliza (Dicionários/Listas)
st.session_state.pizzas = dict(df_pizzas_raw.values) if not df_pizzas_raw.empty else {"Mussarela": 40.0}
st.session_state.bebidas = dict(df_bebidas_raw.values) if not df_bebidas_raw.empty else {"Coca-Cola": 10.0}
st.session_state.bordas = dict(df_bordas_raw.values) if not df_bordas_raw.empty else {"Sem Borda": 0.0}
st.session_state.clientes = df_clientes_raw.to_dict('records') if not df_clientes_raw.empty else []
st.session_state.vendas = df_vendas_raw.to_dict('records') if not df_vendas_raw.empty else []

# Tratamento especial para Promoções (que guarda um dicionário interno de itens)
if not df_promo_raw.empty:
    st.session_state.promocoes = []
    for _, r in df_promo_raw.iterrows():
        st.session_state.promocoes.append({
            "nome": r['nome'],
            "qtd_pizzas": r['qtd_pizzas'],
            "preco_promocional": r['preco_promocional'],
            "entrega_inclusa": r['entrega_inclusa'],
            "itens": {"s1": r['s1_base'], "s2": "Nenhum", "borda": "Sem Borda"}
        })
else:
    st.session_state.promocoes = []

# --- FUNÇÃO PARA GERAR COMANDA PDF ---
def gerar_comanda_pdf(c_nome, lista_itens, total, obs):
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

# --- NAVEGAÇÃO ---
aba = st.sidebar.radio("Navegação:", ["PDV - Pedidos", "Cardápio", "Promoções", "Clientes", "Relatório"])

# --- TELA 1: PDV ---
if aba == "PDV - Pedidos":
    st.header("🛒 Terminal de Vendas")
    
    nome_busca = st.text_input("🔍 Buscar cliente:")
    resultados = [c for c in st.session_state.clientes if nome_busca.lower() in str(c.get('nome', '')).lower()]
    c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x.get('nome', 'Sem Nome')) if resultados else None
    
    if c_sel:
        st.info(f"👤 Cliente: {c_sel.get('nome')} | 📍 {c_sel.get('endereco')}")
        tab_promo, tab_manual = st.tabs(["🎁 Combos", "🍕 Manual"])

        with tab_promo:
            if st.session_state.promocoes:
                p_sel = st.selectbox("Escolha o combo:", st.session_state.promocoes, format_func=lambda x: f"{x['nome']} - R$ {x['preco_promocional']:.2f}")
                if st.button("🚀 Aplicar Combo"):
                    for _ in range(int(p_sel['qtd_pizzas'])):
                        st.session_state.carrinho.append({
                            "s1": p_sel['itens']['s1'], "s2": "Nenhum", "borda": "Sem Borda",
                            "preco": p_sel['preco_promocional']/p_sel['qtd_pizzas'], 
                            "entrega_gratis": p_sel['entrega_inclusa']
                        })
                    st.rerun()

        with tab_manual:
            c1, c2 = st.columns(2)
            s1 = c1.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
            s2 = c2.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()))
            borda = c1.selectbox("Borda", list(st.session_state.bordas.keys()))
            
            p1 = st.session_state.pizzas[s1]
            p2 = st.session_state.pizzas[s2] if s2 != "Nenhum" else p1
            total_item = ((p1+p2)/2) + st.session_state.bordas[borda]
            
            if st.button("🍕 Adicionar Pizza"):
                st.session_state.carrinho.append({"s1": s1, "s2": s2, "borda": borda, "preco": total_item, "entrega_gratis": False})
                st.rerun()

        # Resumo do Carrinho
        if st.session_state.carrinho:
            st.write("### 🛒 Carrinho")
            for i, item in enumerate(st.session_state.carrinho):
                st.write(f"{item['s1']} + {item['s2']} ({item['borda']}) - R$ {item['preco']:.2f}")
            
            tem_gratis = any(i['entrega_gratis'] for i in st.session_state.carrinho)
            taxa = st.number_input("Taxa de Entrega:", value=0.0 if tem_gratis else 8.0)
            total_venda = sum(i['preco'] for i in st.session_state.carrinho) + taxa
            
            if st.button("✅ FINALIZAR VENDA"):
                nova_venda = {"data": datetime.now().strftime("%d/%m/%Y %H:%M"), "cliente": c_sel['nome'], "total": total_venda}
                # Adiciona à lista local e salva na planilha
                st.session_state.vendas.append(nova_venda)
                salvar_dados_sheets(pd.DataFrame(st.session_state.vendas), "vendas")
                
                st.session_state.ultimo_pdf = gerar_comanda_pdf(c_sel['nome'], st.session_state.carrinho, total_venda, "")
                st.success("Venda salva no Google Sheets!")
                st.session_state.carrinho = []
                st.rerun()

# --- TELA: PROMOÇÕES (Alinhado com a margem esquerda) ---
elif aba == "Promoções":
    st.header("🎁 Gestão de Promoções")
    df_promo = ler_dados("promocoes")
    
    # SE A PLANILHA ESTIVER VAZIA, DEFINE AS COLUNAS ESPERADAS
    if df_promo.empty:
        df_promo = pd.DataFrame(columns=["nome", "qtd_pizzas", "preco_promocional", "entrega_inclusa", "s1_base"])
        
    ed_promo = st.data_editor(df_promo, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Promoções"):
        salvar_dados_sheets(ed_promo, "promocoes")
        st.rerun()
# --- TELA: CARDÁPIO (GESTÃO) ---
elif aba == "Cardápio":
    st.header("⚙️ Gestão de Cardápio")
    # Agora incluindo as 3 abas corretamente
    aba_p, aba_b, aba_be = st.tabs(["🍕 Pizzas", "🧀 Bordas", "🥤 Bebidas"])
    
    with aba_p:
        df_p = ler_dados("pizzas")
        ed_p = st.data_editor(df_p, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Salvar Pizzas"):
            salvar_dados_sheets(ed_p, "pizzas")
            st.rerun()

    with aba_be:
        df_be = ler_dados("bebidas")
        ed_be = st.data_editor(df_be, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Salvar Bebidas"):
            salvar_dados_sheets(ed_be, "bebidas")
            st.rerun()

# --- TELA: CLIENTES ---
elif aba == "Clientes":
    st.header("👥 Gestão de Clientes")
    df_c = ler_dados("clientes")
    
    # O data_editor vai mostrar o que veio da planilha
    ed_c = st.data_editor(df_c, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar Clientes"):
        salvar_dados_sheets(ed_c, "clientes")
        st.rerun()
# --- TELA: RELATÓRIO ---
elif aba == "Relatório":
    st.header("📊 Relatório de Vendas")
    if st.session_state.vendas:
        df_v = pd.DataFrame(st.session_state.vendas)
        st.dataframe(df_v, use_container_width=True)
        st.metric("Total Faturado", f"R$ {df_v['total'].sum():.2f}")
    else:
        st.info("Nenhuma venda no sistema.")





