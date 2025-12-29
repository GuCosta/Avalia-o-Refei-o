import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuração da Página
st.set_page_config(page_title="Avaliação de Refeições Online", layout="wide")

# Inicializa conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÃO PARA GERAR O PDF ---
def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "Relatorio de Avaliacao de Refeicoes", ln=True, align="C")
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.ln(10)
    pdf.cell(190, 10, "1. Medias Estatisticas", ln=True)
    pdf.set_font("Helvetica", "", 11)
    
    colunas_notas = ["Aparência", "Aroma", "Sabor", "Textura", "Temperatura", "Porção", "Geral"]
    # Garante que os dados são numéricos para a média
    for col in colunas_notas:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    medias = df[colunas_notas].mean()
    for coluna, valor in medias.items():
        col_clean = coluna.replace("ê", "e").replace("ç", "c").replace("ã", "a")
        pdf.cell(95, 8, f"- {col_clean}:", border=0)
        pdf.cell(95, 8, f"{valor:.2f} / 5.00", border=0, ln=True)
    
    return bytes(pdf.output())

# --- INTERFACE DE ENTRADA ---
st.title("📋 Avaliação de Refeição (Online)")

with st.form("form_avaliacao"):
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", datetime.now())
        avaliador = st.text_input("Avaliador", value="Nicolas Artigas")
        tipo_refeicao = st.selectbox("Tipo de Refeição", ["Almoço", "Jantar", "Café da Manhã", "Lanche"])
    with col2:
        horario = st.time_input("Horário", datetime.now().time())
        setor = st.selectbox("Setor", ["Enfermagem", "Médicos", "Administrativo", "Limpeza", "Segurança", "Laboratório", "Farmácia", "Recepção", "Outros"])
    
    st.subheader("Notas (1 a 5)")
    c1, c2, c3 = st.columns(3)
    with c1:
        aparencia = st.slider("Aparência", 1, 5, 3)
        aroma = st.slider("Aroma", 1, 5, 3)
    with c2:
        sabor = st.slider("Sabor", 1, 5, 3)
        textura = st.slider("Textura", 1, 5, 3)
    with c3:
        temperatura = st.slider("Temperatura", 1, 5, 3)
        porcao = st.slider("Tamanho da Porção", 1, 5, 3)
    
    geral = st.slider("Avaliação Geral", 1, 5, 3)
    consumo = st.select_slider("Percentual Consumido", options=["0%", "25%", "50%", "75%", "100%"], value="100%")
    observacoes = st.text_area("Observações")
    
    submit = st.form_submit_button("Enviar para Planilha Online")

if submit:
    # Ler dados atuais
    existing_data = conn.read(spreadsheet=st.secrets["gsheets_url"])
    
    # Criar nova linha
    nova_linha = pd.DataFrame([{
        "Data": str(data), "Avaliador": avaliador, "Horário": horario.strftime("%H:%M"),
        "Tipo": tipo_refeicao, "Setor": setor, "Aparência": aparencia,
        "Aroma": aroma, "Sabor": sabor, "Textura": textura,
        "Temperatura": temperatura, "Porção": porcao, "Geral": geral,
        "Consumo": consumo, "Observações": observacoes
    }])
    
    # Adicionar e atualizar planilha
    updated_df = pd.concat([existing_data, nova_linha], ignore_index=True)
    conn.update(spreadsheet=st.secrets["gsheets_url"], data=updated_df)
    
    st.success("Dados enviados com sucesso!")

# --- RELATÓRIO ---
st.divider()
try:
    df_cloud = conn.read(spreadsheet=st.secrets["gsheets_url"])
    if not df_cloud.empty:
        st.subheader("📊 Resumo Estatístico")
        st.metric("Total de Avaliações", len(df_cloud))
        
        if st.button("Gerar Relatório PDF"):
            pdf_bytes = gerar_pdf(df_cloud)
            st.download_button("📥 Baixar PDF", data=pdf_bytes, file_name="relatorio_online.pdf", mime="application/pdf")
except:
    st.info("Conecte sua planilha para visualizar as métricas.")