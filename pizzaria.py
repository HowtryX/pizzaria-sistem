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
    
    # 1. Seleção de Cliente
    nome_busca = st.text_input("🔍 Buscar cliente:")
    resultados = [c for c in st.session_state.clientes if nome_busca.lower() in c['nome'].lower()]
    
    if nome_busca and resultados:
        c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x['nome'])
        
        # --- NOVO: APLICAR PROMOÇÃO ---
        # --- BLOCO CORRIGIDO DE APLICAR PROMOÇÃO NO PDV ---
        if st.session_state.promocoes:
            with st.expander("🎁 Aplicar Promoção (Combo)"):
                # Se algum item antigo não tiver 'nome', exibimos "Promoção Antiga"
                p_sel = st.selectbox(
                    "Escolha o combo:", 
                    st.session_state.promocoes, 
                    format_func=lambda x: x.get('nome', 'Promoção Sem Nome')
                )
                
                if st.button("Aplicar Promoção"):
                    for _ in range(p_sel.get('qtd_pizzas', 1)):
                        st.session_state.carrinho.append({
                            "s1": p_sel['itens'].get('s1', 'Mussarela'), 
                            "s2": p_sel['itens'].get('s2', 'Nenhum'), 
                            "borda": p_sel['itens'].get('borda', 'Sem Borda'), 
                            "preco": p_sel.get('preco_promocional', 0.0) / p_sel.get('qtd_pizzas', 1)
                        })
                    st.success(f"Combo aplicado!")
                    st.rerun()

        # --- SELEÇÃO NORMAL ---
        col1, col2 = st.columns(2)
        # ... (seu código de seleção manual de pizzas e bebidas continua aqui) ...

        # --- LÓGICA DO CARRINHO ---
        if st.session_state.carrinho:
            st.write("---")
            st.write("### 🛒 Carrinho")
            
            # Cálculo de Total
            total_pizzas = sum(item['preco'] for item in st.session_state.carrinho)
            
            # --- Lógica da Taxa de Entrega com Promoção ---
            # Se QUALQUER item no carrinho for de uma promoção que inclui entrega, taxa = 0
            taxa_padrao = 8.0
            entrega_gratis = any(p.get('entrega_inclusa', False) for p in st.session_state.promocoes if p.get('nome') in [c.get('nome') for c in st.session_state.carrinho])
            
            taxa_entrega = st.number_input("Taxa de Entrega (R$):", value=0.0 if entrega_gratis else taxa_padrao)
            total = total_pizzas + taxa_entrega
            
            st.subheader(f"💰 Total do Pedido: R$ {total:.2f}")
            
            # Botão FINALIZAR... (seu código de finalização permanece igual)
            
            if st.button("✅ FINALIZAR E IMPRIMIR"):
                nova_venda = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Cliente": c_sel['nome'], "Itens": st.session_state.carrinho, "Total": total, "Obs": obs}
                st.session_state.vendas.append(nova_venda)
                salvar_dados('vendas.json', st.session_state.vendas)
                st.session_state.ultimo_pdf = gerar_comanda_pdf(c_sel['nome'], st.session_state.carrinho, bebs, total, obs)
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
    st.header("🎁 Criar Promoção Personalizada")
    
    with st.expander("➕ Nova Promoção de Combo/Pizza"):
        nome_promo = st.text_input("Nome da Promoção (ex: Combo Casal)")
        # --- NOVO: Campo de Quantidade ---
        qtd_pizzas = st.number_input("Quantidade de Pizzas no combo:", min_value=1, step=1, value=1)
        
        s1 = st.selectbox("Sabor 1", list(st.session_state.pizzas.keys()), key="promo_s1")
        s2 = st.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()), key="promo_s2")
        borda = st.selectbox("Borda:", list(st.session_state.bordas.keys()), key="promo_borda")
        bebs = st.multiselect("Bebidas:", list(st.session_state.bebidas.keys()), key="promo_bebs")
        preco_final = st.number_input("Preço Promocional (R$):", min_value=0.0)
        entrega_inclusa = st.checkbox("Incluir Taxa de Entrega?")
        
        if st.button("Salvar Promoção"):
            nova_promo = {
                "nome": nome_promo or "Promoção Sem Nome",
                "qtd_pizzas": qtd_pizzas, # Salva a quantidade
                "itens": {"s1": s1, "s2": s2, "borda": borda, "bebidas": bebs},
                "preco_promocional": preco_final,
                "entrega_inclusa": entrega_inclusa
            }
            st.session_state.promocoes.append(nova_promo)
            salvar_dados('promocoes.json', st.session_state.promocoes)
            st.success("Promoção criada!")
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
    st.table(pd.DataFrame(st.session_state.vendas))





