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
                            st.rerun()
            # ... (código do expander de promoções que fizemos antes) ...
                
            with tab_manual:
                c1, c2 = st.columns(2)
                s1 = c1.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
                s2 = c2.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()))
                borda = c1.selectbox("Borda:", list(st.session_state.bordas.keys()))
                bebs_selecionadas = c2.multiselect("Bebidas:", list(st.session_state.bebidas.keys()))
            
            # --- CÁLCULO E BOTÃO ---
            # Garantimos que o cálculo ocorra aqui
            preco_pizza = (st.session_state.pizzas[s1] + (st.session_state.pizzas.get(s2, 0) if s2 != "Nenhum" else 0)) / 2
            preco_borda = st.session_state.bordas.get(borda, 0)
            preco_bebs = sum([st.session_state.bebidas.get(b, 0) for b in bebs_selecionadas])
            total_item = preco_pizza + preco_borda + preco_bebs
            
            # O botão precisa estar visível logo abaixo
            if st.button("➕ Adicionar ao Carrinho", key="add_manual"):
                st.session_state.carrinho.append({
                    "s1": s1, 
                    "s2": s2, 
                    "borda": borda, 
                    "bebidas": bebs_selecionadas,
                    "preco": total_item
                })
                st.success(f"Item adicionado! R$ {total_item:.2f}")
                st.rerun()
               
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
    
    tab_p, tab_b, tab_be = st.tabs(["🍕 Pizzas", "🧀 Bordas", "🥤 Bebidas"])

    # --- ABA PIZZAS ---
    with tab_p:
        with st.form("add_pizza", clear_on_submit=True):
            col1, col2 = st.columns(2)
            novo_s = col1.text_input("Nome da Pizza")
            preco_s = col2.number_input("Preço (R$)", min_value=0.0)
            if st.form_submit_button("➕ Adicionar Pizza"):
                if novo_s:
                    st.session_state.pizzas[novo_s] = preco_s
                    salvar_dados('pizzas.json', st.session_state.pizzas)
                    st.success(f"{novo_s} adicionada!")
                    st.rerun()

        st.write("---")
        df_p = pd.DataFrame(list(st.session_state.pizzas.items()), columns=["Sabor", "Preço"])
        st.dataframe(df_p, use_container_width=True)

    # --- ABA BORDAS ---
    with tab_b:
        with st.form("add_borda", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nova_b = col1.text_input("Tipo de Borda")
            preco_b = col2.number_input("Preço Adicional (R$)", min_value=0.0)
            if st.form_submit_button("➕ Adicionar Borda"):
                if nova_b:
                    st.session_state.bordas[nova_b] = preco_b
                    salvar_dados('bordas.json', st.session_state.bordas)
                    st.rerun()
        
        df_b = pd.DataFrame(list(st.session_state.bordas.items()), columns=["Borda", "Preço"])
        st.table(df_b)

    # --- ABA BEBIDAS ---
    with tab_be:
        with st.form("add_bebida", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nova_be = col1.text_input("Nome da Bebida")
            preco_be = col2.number_input("Preço Unidade (R$)", min_value=0.0)
            if st.form_submit_button("➕ Adicionar Bebida"):
                if nova_be:
                    st.session_state.bebidas[nova_be] = preco_be
                    salvar_dados('bebidas.json', st.session_state.bebidas)
                    st.rerun()
        
        df_be = pd.DataFrame(list(st.session_state.bebidas.items()), columns=["Bebida", "Preço"])
        st.dataframe(df_be, use_container_width=True)

# --- TELA: CLIENTES ---
elif aba == "Clientes":
    st.header("👥 Cadastro de Clientes")
    
    # Formulário de Cadastro
    with st.form("cad_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n = col1.text_input("Nome Completo")
        t = col2.text_input("Telefone / WhatsApp")
        e = st.text_area("Endereço de Entrega")
        
        btn_cadastrar = st.form_submit_button("💾 Salvar Cliente")
        
        if btn_cadastrar:
            if n and t: # Validação simples para não salvar vazio
                novo_cliente = {"nome": n, "telefone": t, "endereco": e}
                
                # 1. Adiciona na memória (Session State)
                st.session_state.clientes.append(novo_cliente)
                
                # 2. Grava no arquivo físico IMEDIATAMENTE
                salvar_dados('clientes.json', st.session_state.clientes)
                
                st.success(f"✅ Cliente {n} cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ Nome e Telefone são obrigatórios!")

    # Exibição da Tabela de Clientes
    st.write("---")
    st.subheader("Lista de Clientes Cadastrados")
    
    if st.session_state.clientes:
        df_clientes = pd.DataFrame(st.session_state.clientes)
        # Reordenando as colunas para ficar mais bonito
        st.dataframe(df_clientes[["nome", "telefone", "endereco"]], use_container_width=True)
        
        # Opção para limpar a lista (CUIDADO)
        if st.button("🗑️ Apagar Todos os Clientes"):
            st.session_state.clientes = []
            salvar_dados('clientes.json', [])
            st.rerun()
    else:
        st.info("Nenhum cliente cadastrado ainda.")

# --- TELA 3: PROMOÇÕES ---
elif aba == "Promoções":
    st.header("🎁 Gestão de Promoções")
    
    with st.form("cad_promo", clear_on_submit=True):
        nome_p = st.text_input("Nome do Combo (Ex: Combo Família)")
        col1, col2 = st.columns(2)
        qtd_p = col1.number_input("Qtd de Pizzas no Combo", min_value=1, value=2)
        preco_p = col2.number_input("Preço Total do Combo (R$)", min_value=0.0)
        
        c1, c2 = st.columns(2)
        s1_p = c1.selectbox("Sabor Padrão 1", list(st.session_state.pizzas.keys()))
        ent_p = c2.checkbox("Entrega Grátis neste Combo?")
        
        if st.form_submit_button("💾 Salvar Promoção"):
            nova_promo = {
                "nome": nome_p or "Combo Especial",
                "qtd_pizzas": qtd_p,
                "itens": {"s1": s1_p, "s2": "Nenhum", "borda": "Sem Borda"},
                "preco_promocional": preco_p,
                "entrega_inclusa": ent_p
            }
            st.session_state.promocoes.append(nova_promo)
            salvar_dados('promocoes.json', st.session_state.promocoes)
            st.success("Promoção Gravada!")
            st.rerun()

    st.write("---")
    st.subheader("Promoções Ativas")
    for i, p in enumerate(st.session_state.promocoes):
        with st.container(border=True):
            c_info, c_del = st.columns([4, 1])
            c_info.write(f"**{p.get('nome')}** - {p.get('qtd_pizzas')} Pizzas por R$ {p.get('preco_promocional'):.2f}")
            if c_del.button("🗑️", key=f"del_promo_{i}"):
                st.session_state.promocoes.pop(i)
                salvar_dados('promocoes.json', st.session_state.promocoes)
                st.rerun()

# --- TELA: RELATÓRIO ---
elif aba == "Relatório":
    st.header("📊 Vendas")
    st.dataframe(pd.DataFrame(st.session_state.vendas))






















