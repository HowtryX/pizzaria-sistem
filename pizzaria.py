import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF
import base64

# --- FUNÇÕES DE SEGURANÇA PARA DADOS ---
def carregar_dados(arquivo, padrao):
    """Carrega dados de um arquivo JSON com tratamento de erro."""
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return padrao
    return padrao

def salvar_dados(arquivo, dados):
    """Salva dados em arquivo com segurança contra corrupção."""
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

# Inicialização com carga de arquivos
if 'carrinho' not in st.session_state: st.session_state.carrinho = []
st.session_state.clientes = carregar_dados('clientes.json', [])
st.session_state.pizzas = carregar_dados('pizzas.json', {"Mussarela": 40.0})
st.session_state.bebidas = carregar_dados('bebidas.json', {"Coca-Cola": 10.0})
st.session_state.bordas = carregar_dados('bordas.json', {"Sem Borda": 0.0, "Catupiry": 10.0})
st.session_state.promocoes = carregar_dados('promocoes.json', [])
st.session_state.vendas = carregar_dados('vendas.json', [])

# --- NAVEGAÇÃO ---
aba = st.sidebar.radio("Navegação:", ["PDV - Pedidos", "Cardápio", "Promoções", "Clientes", "Relatório"])

# --- TELA: PDV ---
if aba == "PDV - Pedidos":
    st.header("🛒 Terminal de Vendas")
    nome_busca = st.text_input("🔍 Buscar cliente:")
    resultados = [c for c in st.session_state.clientes if nome_busca.lower() in c.get('nome', '').lower()]
    c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x.get('nome', 'Sem Nome')) if resultados else None

    if not resultados and nome_busca:
        st.warning("⚠️ Cliente não encontrado. Cadastre-o na aba Clientes.")
    
    if c_sel:
        st.info(f"👤 Cliente: {c_sel.get('nome')} | 📍 {c_sel.get('endereco', 'Endereço não cadastrado')}")
        tab_promo, tab_manual = st.tabs(["🎁 Combos/Promoções", "🍕 Seleção Manual"])

        with tab_promo:
            if st.session_state.promocoes:
                p_sel = st.selectbox("Escolha o combo desejado:", st.session_state.promocoes, format_func=lambda x: f"{x.get('nome')} - R$ {x.get('preco_promocional', 0):.2f}")
                if st.button("🚀 Aplicar Este Combo"):
                    qtd = p_sel.get('qtd_pizzas', 1)
                    preco_unitario = p_sel.get('preco_promocional', 0.0) / qtd
                    for _ in range(qtd):
                        st.session_state.carrinho.append({
                            "s1": p_sel.get('itens', {}).get('s1', 'Mussarela'), 
                            "s2": p_sel.get('itens', {}).get('s2', 'Nenhum'), 
                            "borda": p_sel.get('itens', {}).get('borda', 'Sem Borda'), 
                            "preco": preco_unitario, "entrega_gratis": p_sel.get('entrega_inclusa', False), "tipo": "Promoção"
                        })
                    st.rerun()
            else:
                st.info("Nenhuma promoção cadastrada.")

        with tab_manual:
            c1, c2 = st.columns(2)
            s1_m = c1.selectbox("Sabor 1", list(st.session_state.pizzas.keys()))
            s2_m = c2.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()))
            borda_m = c1.selectbox("Borda:", list(st.session_state.bordas.keys()))
            bebs_m = c2.multiselect("Bebidas:", list(st.session_state.bebidas.keys()))
            
            p1 = st.session_state.pizzas.get(s1_m, 0)
            p2 = st.session_state.pizzas.get(s2_m, 0) if s2_m != "Nenhum" else p1
            total_m = ((p1 + p2) / 2) + st.session_state.bordas.get(borda_m, 0) + sum([st.session_state.bebidas.get(b, 0) for b in bebs_m])
            
            if st.button("🍕 Adicionar Pizza Manual"):
                st.session_state.carrinho.append({"s1": s1_m, "s2": s2_m, "borda": borda_m, "bebidas": bebs_m, "preco": total_m, "tipo": "Manual", "entrega_gratis": False})
                st.rerun()

 st.write("---")
st.write("### 🛒 Carrinho")

# --- BLOCO 1: SE HOUVER PDF GERADO (Modo Impressão) ---
# Priorizamos o PDF, pois se ele existe, a venda acabou de ser feita
if 'ultimo_pdf' in st.session_state:
    st.success("✅ Venda finalizada com sucesso!")
    
    with open(st.session_state.ultimo_pdf, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="text-decoration:none;">'
        f'<button style="width:100%; cursor:pointer; background-color:#28a745; color:white; border:none; padding:15px; border-radius:5px; font-size:16px;">'
        f'🖨️ ABRIR COMANDA PARA IMPRIMIR'
        f'</button></a>', unsafe_allow_html=True
    )
    
    # Único botão de reset aqui
    if st.button("🔄 Novo Pedido", key="btn_resetar"):
        if os.path.exists(st.session_state.ultimo_pdf):
            os.remove(st.session_state.ultimo_pdf) # Opcional: deleta o arquivo físico
        del st.session_state.ultimo_pdf
        st.rerun()

# --- BLOCO 2: SE O CARRINHO TEM ITENS (Modo Venda Ativa) ---
elif st.session_state.carrinho:
    for i, item in enumerate(st.session_state.carrinho):
        col_nome, col_preco, col_btn = st.columns([3, 1, 1])
        col_nome.write(f"**{item.get('s1')}** / {item.get('s2')} ({item.get('borda')})")
        col_preco.write(f"R$ {item.get('preco', 0):.2f}")
        if col_btn.button("🗑️", key=f"del_{i}"):
            st.session_state.carrinho.pop(i)
            st.rerun()

    total_pizzas = sum(item.get('preco', 0) for item in st.session_state.carrinho)
    taxa = st.number_input("Taxa de Entrega (R$):", value=0.0 if any(i.get('entrega_gratis') for i in st.session_state.carrinho) else 8.0)
    total_geral = total_pizzas + taxa
    st.subheader(f"💰 Total Geral: R$ {total_geral:.2f}")

    if st.button("✅ FINALIZAR VENDA", key="btn_finalizar"):
        venda_final = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"), 
            "cliente": c_sel.get('nome'), 
            "total": total_geral, 
            "itens": st.session_state.carrinho.copy()
        }
        st.session_state.vendas.append(venda_final)
        salvar_dados('vendas.json', st.session_state.vendas)
        
        # Gera o PDF
        st.session_state.ultimo_pdf = gerar_comanda_pdf(c_sel['nome'], st.session_state.carrinho, [], total_geral, "")
        st.session_state.carrinho = [] # Limpa carrinho
        st.rerun()

# --- BLOCO 3: CARRINHO VAZIO (Estado inicial) ---
else:
    st.info("O carrinho está vazio. Adicione itens para iniciar um pedido.")
# --- TELA: CARDÁPIO ---
elif aba == "Cardápio":
    st.header("⚙️ Gestão de Cardápio")
    tab_p, tab_b, tab_be = st.tabs(["🍕 Pizzas", "🧀 Bordas", "🥤 Bebidas"])

    def gerenciar(titulo, chave, arquivo, nome_col):
        df = pd.DataFrame(list(st.session_state[chave].items()), columns=[nome_col, "Preço"])
        editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button(f"💾 Salvar {titulo}"):
            st.session_state[chave] = {row[nome_col]: row["Preço"] for _, row in editado.iterrows() if row[nome_col]}
            salvar_dados(arquivo, st.session_state[chave])
            st.rerun()

    with tab_p: gerenciar("Pizzas", "pizzas", "pizzas.json", "Sabor")
    with tab_b: gerenciar("Bordas", "bordas", "bordas.json", "Tipo de Borda")
    with tab_be: gerenciar("Bebidas", "bebidas", "bebidas.json", "Bebida")

# --- TELA: CLIENTES ---
elif aba == "Clientes":
    st.header("👥 Gestão de Clientes")
    df = st.data_editor(pd.DataFrame(st.session_state.clientes), num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Clientes"):
        st.session_state.clientes = [c for c in df.to_dict('records') if c.get('nome')]
        salvar_dados('clientes.json', st.session_state.clientes)
        st.rerun()

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
        # Proteção contra erros de chave com .get()
        nome = p.get('nome', 'Promoção')
        qtd = p.get('qtd_pizzas', 1) # Padrão 1 se não existir
        itens = p.get('itens', {})
        preco = p.get('preco_promocional', 0.0)
        entrega = p.get('entrega_inclusa', False)
        
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"### {nome}")
            col1.write(f"🍕 **Quantidade:** {qtd} pizza(s) | Sabor: {itens.get('s1')} + {itens.get('s2')}")
            col1.write(f"🥤 Bebidas: {', '.join(itens.get('bebidas', [])) if itens.get('bebidas') else 'Nenhuma'}")
            col1.subheader(f"💰 Preço: R$ {preco:.2f}")
            
            # Label de entrega
            if entrega: col1.success("🚚 Entrega Grátis!")
            
            if col2.button("🗑️", key=f"del_p_{i}"):
                st.session_state.promocoes.pop(i)
                salvar_dados('promocoes.json', st.session_state.promocoes)
                st.rerun()

# --- TELA: RELATÓRIO ---
elif aba == "Relatório":
    st.header("📊 Vendas")
    st.dataframe(pd.DataFrame(st.session_state.vendas))















