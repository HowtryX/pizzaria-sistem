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
        if item.get('bebidas'):
            pdf.set_font("Arial", size=9)
            pdf.cell(62, 5, txt=f"Bebidas: {', '.join(item['bebidas'])}", ln=True)
    
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
    
    # 1. Busca de Cliente
    nome_busca = st.text_input("🔍 Buscar cliente:")
    resultados = [c for c in st.session_state.clientes if nome_busca.lower() in c.get('nome', '').lower()]
    c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x['nome']) if resultados else None
    
    if c_sel:
        # 2. Abas de Seleção
        tab_promo, tab_manual = st.tabs(["🎁 Combos", "🍕 Seleção Manual"])
        
               with tab_promo:
                   if st.session_state.promocoes:
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
                    s    t.rerun()
            # ... (código do expander de promoções que fizemos antes) ...
                
            with tab_manual:
                c1, c2 = st.columns(2)
                s1 = c1.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
                s2 = c2.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()))
                borda = c1.selectbox("Borda:", list(st.session_state.bordas.keys()))
                bebs_selecionadas = c2.multiselect("Bebidas:", list(st.session_state.bebidas.keys()))
            # ... (código da seleção de pizza + bebidas que fizemos antes) ...

        # 3. CARRINHO (Aparece sempre que houver cliente selecionado)
        st.write("---")
        st.write("### 🛒 Carrinho")
        
        # Exibição do carrinho com Botão de Remover
        for i, item in enumerate(st.session_state.carrinho):
            col_nome, col_preco, col_btn = st.columns([3, 1, 1])
            col_nome.write(f"{item.get('s1')} + {item.get('s2')} | {item.get('borda')}")
            col_preco.write(f"R$ {item.get('preco', 0):.2f}")
            if col_btn.button("🗑️", key=f"del_c_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()

        # 4. Total e Finalização
        if st.session_state.carrinho:
            total_pizzas = sum(item.get('preco', 0) for item in st.session_state.carrinho)
            taxa = st.number_input("Taxa de Entrega (R$):", value=8.0)
            total_geral = total_pizzas + taxa
            st.subheader(f"💰 Total: R$ {total_geral:.2f}")

            # Botões de Ação
            col_f, col_n = st.columns(2)
            if col_f.button("✅ FINALIZAR E IMPRIMIR"):
                st.session_state.ultimo_pdf = gerar_comanda_pdf(c_sel['nome'], st.session_state.carrinho, [], total_geral, "")
                st.session_state.vendas.append({"Cliente": c_sel['nome'], "Itens": st.session_state.carrinho, "Total": total_geral})
                salvar_dados('vendas.json', st.session_state.vendas)
                st.rerun()
                
            if 'ultimo_pdf' in st.session_state:
                with open(st.session_state.ultimo_pdf, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank">🖨️ IMPRIMIR COMANDA</a>', unsafe_allow_html=True)
                
                if col_n.button("🔄 INICIAR NOVO PEDIDO"):
                    st.session_state.carrinho = []
                    if 'ultimo_pdf' in st.session_state: del st.session_state.ultimo_pdf
                    st.rerun()

# --- TELA: CARDÁPIO ---
# --- TELA: CARDÁPIO (GESTÃO COMPLETA) ---
elif aba == "Cardápio":
    st.header("⚙️ Gestão de Cardápio")
    
    # Criamos abas para cada categoria
    tab1, tab2, tab3 = st.tabs(["🍕 Pizzas", "🧀 Bordas", "🥤 Bebidas"])
    
    # Função auxiliar para editar qualquer categoria
    def editar_categoria(titulo, chave_session, arquivo):
        st.subheader(f"Gerenciar {titulo}")
        df = pd.DataFrame(list(st.session_state[chave_session].items()), columns=["Item", "Preço"])
        edited_df = st.data_editor(df, num_rows="dynamic")
        
        if st.button(f"💾 Salvar {titulo}", key=f"btn_{chave_session}"):
            st.session_state[chave_session] = dict(zip(edited_df["Item"], edited_df["Preço"]))
            salvar_dados(arquivo, st.session_state[chave_session])
            st.success(f"{titulo} atualizado com sucesso!")
            st.rerun()

    with tab1:
        editar_categoria("Pizzas", "pizzas", "pizzas.json")
    with tab2:
        editar_categoria("Bordas", "bordas", "bordas.json")
    with tab3:
        editar_categoria("Bebidas", "bebidas", "bebidas.json")

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
# --- TELA 3: PROMOÇÕES (SUBSTITUA TODO O BLOCO) ---
elif aba == "Promoções":
    st.header("🎁 Criar Promoção")
    
    with st.expander("➕ Nova Promoção"):
        nome = st.text_input("Nome da Promoção")
        qtd = st.number_input("Qtd Pizzas", min_value=1, value=1)
        s1 = st.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
        s2 = st.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()))
        borda = st.selectbox("Borda:", list(st.session_state.bordas.keys()))
        preco = st.number_input("Preço Promocional", min_value=0.0)
        ent = st.checkbox("Entrega Grátis?")
        
        if st.button("Salvar Promoção"):
            nova_promo = {
                "nome": nome or "Promoção Sem Nome",
                "qtd_pizzas": qtd,
                "itens": {"s1": s1, "s2": s2, "borda": borda},
                "preco_promocional": preco,
                "entrega_inclusa": ent
            }
            st.session_state.promocoes.append(nova_promo)
            salvar_dados('promocoes.json', st.session_state.promocoes)
            st.success("Promoção salva!")
            st.rerun()
    
    st.subheader("Promoções Ativas")
    # Apenas um loop de exibição para evitar duplicidade
    for i, p in enumerate(st.session_state.promocoes):
        # Proteção com .get() para evitar KeyError
        nome = p.get('nome', 'Promoção Sem Nome')
        qtd = p.get('qtd_pizzas', 1)
        itens = p.get('itens', {})
        preco = p.get('preco_promocional', 0.0)
        
        with st.container(border=True):
            col_info, col_del = st.columns([5, 1])
            col_info.markdown(f"### {nome}")
            col_info.write(f"🍕 Qtd: {qtd} | Sabores: {itens.get('s1')} + {itens.get('s2')} | Borda: {itens.get('borda')}")
            col_info.subheader(f"💰 Preço: R$ {preco:.2f}")
            
            if col_del.button("🗑️", key=f"del_promo_{i}"):
                st.session_state.promocoes.pop(i)
                salvar_dados('promocoes.json', st.session_state.promocoes)
                st.rerun()

# --- TELA: RELATÓRIO ---
elif aba == "Relatório":
    st.header("📊 Vendas")
    st.dataframe(pd.DataFrame(st.session_state.vendas))













