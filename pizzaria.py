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
if aba == "PDV - Pedidos":
  st.header("🛒 Terminal de Vendas")

  # 1. Busca de Cliente
nome_busca = st.text_input("🔍 Buscar cliente:")
resultados = [c for c in st.session_state.clientes if nome_busca.lower() in c.get('nome', '').lower()]

  # Selectbox de cliente
  c_sel = st.selectbox("Selecione o cliente:", resultados, format_func=lambda x: x.get('nome', 'Sem Nome')) if resultados else None

    if not resultados and nome_busca:
      st.warning("⚠️ Cliente não encontrado. Cadastre-o na aba Clientes.")
    
    if c_sel:
      st.info(f"👤 Cliente: {c_sel.get('nome')} | 📍 {c_sel.get('endereco', 'Endereço não cadastrado')}")
      
      # 2. SELEÇÃO DE ITENS
      st.subheader("➕ Adicionar ao Pedido")
          tab_promo, tab_manual = st.tabs(["🎁 Combos/Promoções", "🍕 Seleção Manual"])

          with tab_promo:
            if st.session_state.promocoes:
              p_sel = st.selectbox(
                "Escolha o combo desejado:",
                  st.session_state.promocoes,
                      format_func=lambda x: f"{x.get('nome')} - R$ {x.get('preco_promocional', 0):.2f}",
                key="sb_promo_pdv"
              )
              
              if st.button("🚀 Aplicar Este Combo", key="btn_aplicar_promo"):
                qtd = p_sel.get('qtd_pizzas', 1)
                preco_unitario = p_sel.get('preco_promocional', 0.0) / qtd
                
                for _ in range(qtd):
                  st.session_state.carrinho.append({
                    "s1": p_sel.get('itens', {}).get('s1', 'Mussarela'),
                    "s2": p_sel.get('itens', {}).get('s2', 'Nenhum'),
                    "borda": p_sel.get('itens', {}).get('borda', 'Sem Borda'),
                    "preco": preco_unitario,
                    "entrega_gratis": p_sel.get('entrega_inclusa', False),
                    "tipo": "Promoção"
                  })
                  st.success(f"✅ Combo '{p_sel.get('nome')}' adicionado!")
                  st.rerun()
              else:
                st.info("Nenhuma promoção cadastrada.")

        with tab_manual:
            c1, c2 = st.columns(2)
            s1_m = c1.selectbox("Sabor 1", list(st.session_state.pizzas.keys()), key="sb_s1_manual")
            s2_m = c2.selectbox("Sabor 2", ["Nenhum"] + list(st.session_state.pizzas.keys()), key="sb_s2_manual")
            borda_m = c1.selectbox("Borda:", list(st.session_state.bordas.keys()), key="sb_borda_manual")
            bebs_m = c2.multiselect("Bebidas:", list(st.session_state.bebidas.keys()), key="ms_bebs_manual")
            
            # Cálculo Manual
            p1 = st.session_state.pizzas.get(s1_m, 0)
            p2 = st.session_state.pizzas.get(s2_m, 0) if s2_m != "Nenhum" else p1
            preco_pizza = (p1 + p2) / 2
            preco_borda = st.session_state.bordas.get(borda_m, 0)
            preco_bebs = sum([st.session_state.bebidas.get(b, 0) for b in bebs_m])
            
            total_m = preco_pizza + preco_borda + preco_bebs
            
            if st.button("🍕 Adicionar Pizza Manual", key="btn_add_manual"):
                st.session_state.carrinho.append({
                    "s1": s1_m, "s2": s2_m, "borda": borda_m, 
                    "bebidas": bebs_m, "preco": total_m, "tipo": "Manual",
                    "entrega_gratis": False
                })
                st.success("✅ Item adicionado ao carrinho!")
                st.rerun()

        # 3. CARRINHO
        st.write("---")
        st.write("### 🛒 Carrinho")
        
        if not st.session_state.carrinho:
            st.write("O carrinho está vazio.")
        else:
            for i, item in enumerate(st.session_state.carrinho):
                col_nome, col_preco, col_btn = st.columns([3, 1, 1])
                info_item = f"**{item.get('s1')}**"
                if item.get('s2') != "Nenhum": info_item += f" / {item.get('s2')}"
                info_item += f" ({item.get('borda')})"
                
                col_nome.write(info_item)
                col_preco.write(f"R$ {item.get('preco', 0):.2f}")
                if col_btn.button("🗑️", key=f"del_c_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()

            # 4. Total e Finalização
            st.write("---")
            total_pizzas = sum(item.get('preco', 0) for item in st.session_state.carrinho)
            
            # Lógica de Entrega Grátis: se houver QUALQUER item de promoção com entrega grátis, o valor padrão é 0
            tem_entrega_gratis = any(item.get('entrega_gratis', False) for item in st.session_state.carrinho)
            taxa_padrao = 0.0 if tem_entrega_gratis else 8.0
            
            taxa = st.number_input("Taxa de Entrega (R$):", value=taxa_padrao)
            total_geral = total_pizzas + taxa
            st.subheader(f"💰 Total Geral: R$ {total_geral:.2f}")

            col_f, col_n = st.columns(2)
            
            if col_f.button("✅ FINALIZAR E IMPRIMIR", use_container_width=True):
                # Gerar venda para o relatório
                venda_final = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "cliente": c_sel.get('nome'),
                    "total": total_geral,
                    "itens": st.session_state.carrinho.copy()
                }
                st.session_state.vendas.append(venda_final)
                salvar_dados('vendas.json', st.session_state.vendas)
                
                # Gerar PDF
                st.session_state.ultimo_pdf = gerar_comanda_pdf(c_sel['nome'], st.session_state.carrinho, [], total_geral, "")
                st.success("Venda realizada com sucesso!")
                st.rerun()

            if 'ultimo_pdf' in st.session_state:
                with open(st.session_state.ultimo_pdf, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="text-decoration:none;"><button style="width:100%; cursor:pointer; background-color:#28a745; color:white; border:none; padding:10px; border-radius:5px;">🖨️ BAIXAR/IMPRIMIR COMANDA</button></a>', unsafe_allow_html=True)
                
                if col_n.button("🔄 NOVO PEDIDO", use_container_width=True):
                    st.session_state.carrinho = []
                    if 'ultimo_pdf' in st.session_state: del st.session_state.ultimo_pdf
                    st.rerun()

# --- TELA: CARDÁPIO ---
# --- TELA: CARDÁPIO (GESTÃO COMPLETA) ---
# --- TELA: CARDÁPIO (EDIÇÃO E EXCLUSÃO) ---
elif aba == "Cardápio":
    st.header("⚙️ Gestão de Cardápio")
    
    tab_p, tab_b, tab_be = st.tabs(["🍕 Pizzas", "🧀 Bordas", "🥤 Bebidas"])

    # Função Auxiliar para Gerenciar Categorias (Evita repetição de código)
    def gerenciar_categoria(titulo, chave_session, arquivo, col_nome):
        st.subheader(f"Gerenciar {titulo}")
        
        # Converte o dicionário em DataFrame para o editor
        df = pd.DataFrame(list(st.session_state[chave_session].items()), columns=[col_nome, "Preço"])
        
        st.info(f"💡 Dica: Clique duas vezes na célula para EDITAR. Selecione a linha e aperte 'Delete' ou use o ícone de lixo para APAGAR.")
        
        # O data_editor permite editar, adicionar e deletar linhas nativamente
        df_editado = st.data_editor(
            df, 
            num_rows="dynamic", # Permite adicionar e apagar linhas
            use_container_width=True,
            key=f"editor_{chave_session}"
        )
        
        if st.button(f"💾 Salvar Alterações em {titulo}", key=f"save_{chave_session}"):
            # Converte de volta para dicionário e salva
            # Remove linhas vazias ou com nome nulo
            novo_dict = {row[col_nome]: row["Preço"] for _, row in df_editado.iterrows() if row[col_nome]}
            
            st.session_state[chave_session] = novo_dict
            salvar_dados(arquivo, st.session_state[chave_session])
            st.success(f"✅ {titulo} atualizado e salvo permanentemente!")
            st.rerun()

    with tab_p:
        gerenciar_categoria("Pizzas", "pizzas", "pizzas.json", "Sabor")

    with tab_b:
        gerenciar_categoria("Bordas", "bordas", "bordas.json", "Tipo de Borda")

    with tab_be:
        gerenciar_categoria("Bebidas", "bebidas", "bebidas.json", "Bebida")

# --- TELA: CLIENTES ---
# --- TELA: CLIENTES (EDIÇÃO E EXCLUSÃO) ---
elif aba == "Clientes":
    st.header("👥 Gestão de Clientes")
    
    # 1. Formulário para Novo Cadastro (Opcional, mas mantém a organização)
    with st.expander("➕ Cadastrar Novo Cliente"):
        with st.form("form_novo_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome")
            t = c2.text_input("Telefone")
            e = st.text_area("Endereço")
            if st.form_submit_button("Salvar Novo Cliente"):
                if n and t:
                    st.session_state.clientes.append({"nome": n, "telefone": t, "endereco": e})
                    salvar_dados('clientes.json', st.session_state.clientes)
                    st.success(f"Cliente {n} cadastrado!")
                    st.rerun()
                else:
                    st.error("Nome e Telefone são obrigatórios.")

    st.write("---")
    st.subheader("📋 Lista de Clientes")
    st.info("💡 **Como editar/apagar:** Clique nas células para alterar dados. Selecione a linha e aperte 'Delete' no teclado para remover um cliente.")

    # 2. Editor de Dados para Editar e Apagar
    if st.session_state.clientes:
        # Criamos o DataFrame
        df_clientes = pd.DataFrame(st.session_state.clientes)
        
        # Editor interativo
        df_editado = st.data_editor(
            df_clientes,
            num_rows="dynamic", # Permite deletar e adicionar linhas
            use_container_width=True,
            key="editor_clientes"
        )
        
        # 3. Botão para Salvar Alterações Permanentemente
        if st.button("💾 Salvar Alterações na Lista"):
            # Converte o DataFrame editado de volta para lista de dicionários
            nova_lista = df_editado.to_dict('records')
            
            # Remove entradas totalmente vazias (caso o usuário adicione linha e não preencha)
            st.session_state.clientes = [c for c in nova_lista if c.get('nome')]
            
            salvar_dados('clientes.json', st.session_state.clientes)
            st.success("✅ Lista de clientes atualizada com sucesso!")
            st.rerun()
    else:
        st.warning("Nenhum cliente cadastrado no sistema.")
# --- TELA 3: PROMOÇÕES ---
# --- TELA: PROMOÇÕES (EDIÇÃO E EXCLUSÃO) ---
elif aba == "Promoções":
    st.header("🎁 Gestão de Promoções")

    # 1. Formulário para Nova Promoção
    with st.expander("➕ Criar Novo Combo / Promoção"):
        with st.form("form_nova_promo", clear_on_submit=True):
            nome_p = st.text_input("Nome do Combo")
            c1, c2, c3 = st.columns(3)
            qtd_p = c1.number_input("Qtd Pizzas", min_value=1, value=1)
            preco_p = c2.number_input("Preço Total (R$)", min_value=0.0)
            ent_p = c3.checkbox("Entrega Grátis?")
            
            s1_p = st.selectbox("Sabor Base", list(st.session_state.pizzas.keys()))
            
            if st.form_submit_button("Salvar Promoção"):
                nova_promo = {
                    "nome": nome_p or "Combo Novo",
                    "qtd_pizzas": qtd_p,
                    "itens": {"s1": s1_p, "s2": "Nenhum", "borda": "Sem Borda"},
                    "preco_promocional": preco_p,
                    "entrega_inclusa": ent_p
                }
                st.session_state.promocoes.append(nova_promo)
                salvar_dados('promocoes.json', st.session_state.promocoes)
                st.success("Promoção cadastrada!")
                st.rerun()

    st.write("---")
    st.subheader("📋 Promoções Ativas")
    st.info("💡 Edite os valores diretamente na tabela ou selecione a linha e aperte 'Delete' para apagar.")

    if st.session_state.promocoes:
        # Preparamos os dados para a tabela (extraindo o que está dentro de 'itens')
        dados_promo = []
        for p in st.session_state.promocoes:
            dados_promo.append({
                "Nome": p.get('nome'),
                "Qtd Pizzas": p.get('qtd_pizzas'),
                "Preço": p.get('preco_promocional'),
                "Entrega Grátis": p.get('entrega_inclusa'),
                "Sabor Base": p.get('itens', {}).get('s1')
            })
        
        df_promo = pd.DataFrame(dados_promo)
        
        # Editor de Dados
        df_editado = st.data_editor(
            df_promo,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_promocoes"
        )
        
        # 2. Botão para Salvar Alterações
        if st.button("💾 Salvar Alterações em Promoções"):
            nova_lista_promos = []
            for _, row in df_editado.iterrows():
                if row["Nome"]: # Evita salvar linhas vazias
                    nova_lista_promos.append({
                        "nome": row["Nome"],
                        "qtd_pizzas": row["Qtd Pizzas"],
                        "preco_promocional": row["Preço"],
                        "entrega_inclusa": row["Entrega Grátis"],
                        "itens": {"s1": row["Sabor Base"], "s2": "Nenhum", "borda": "Sem Borda"}
                    })
            
            st.session_state.promocoes = nova_lista_promos
            salvar_dados('promocoes.json', st.session_state.promocoes)
            st.success("✅ Promoções atualizadas!")
            st.rerun()
    else:
        st.warning("Nenhuma promoção ativa.")
# --- TELA: RELATÓRIO ---
elif aba == "Relatório":
    st.header("📊 Vendas")
    st.dataframe(pd.DataFrame(st.session_state.vendas))
















