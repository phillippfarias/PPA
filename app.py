import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(layout="wide")

# -------- EXTRAÇÃO DO PDF --------
def extract_text(files):
    linhas = []

    for file in files:
        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()

                if text:
                    for line in text.split("\n"):
                        linhas.append({
                            "page": page_num + 1,
                            "text": line.strip()
                        })

    return pd.DataFrame(linhas)


# -------- PARSER DO PPA (AJUSTADO AO SEU PDF) --------
def parse_ppa(df):

    estrutura = []

    eixo = tema = programa = objetivo = None

    for _, row in df.iterrows():
        line = row["text"].strip()
        line_upper = line.upper()

        # -------- EIXO --------
        if re.match(r"^\d+\s*-\s*O CEARÁ", line_upper):
            eixo = line
            tema = programa = objetivo = None

        # -------- TEMA --------
        elif re.match(r"^\d+\.\d+\s*-", line):
            tema = line
            programa = objetivo = None

        # -------- PROGRAMA --------
        elif re.match(r"^\d{3,}\s*-", line):
            programa = line
            objetivo = None

        # -------- OBJETIVO --------
        elif "OBJETIVO ESPECÍFICO" in line_upper:
            objetivo = line

        # -------- ENTREGA --------
        elif line_upper.startswith("BENEFÍCIO") or line_upper.startswith("GEOCADASTRO") or "ENTREGA" in line_upper:
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo": objetivo,
                "Entrega": line,
                "Ação": None
            })

        # -------- AÇÃO --------
        elif re.match(r"^\d{4,}\s*-", line):
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo": objetivo,
                "Entrega": None,
                "Ação": line
            })

    return pd.DataFrame(estrutura)


# -------- INTERFACE --------
st.title("Mapa Interativo do PPA - Ceará")

uploaded_files = st.file_uploader(
    "Envie os PDFs do PPA",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    with st.spinner("Lendo PDFs..."):
        df_texto = extract_text(uploaded_files)

    with st.spinner("Estruturando dados..."):
        df = parse_ppa(df_texto)

    if df.empty:
        st.error("Não foi possível identificar a estrutura. Me envie um trecho maior do PDF para ajustar o parser.")
    else:
        st.success("PPA estruturado com sucesso!")

        # -------- FILTROS HIERÁRQUICOS --------
        eixo_sel = st.selectbox("Eixo", sorted(df["Eixo"].dropna().unique()))

        df1 = df[df["Eixo"] == eixo_sel]

        tema_sel = st.selectbox("Tema", sorted(df1["Tema"].dropna().unique()))

        df2 = df1[df1["Tema"] == tema_sel]

        prog_sel = st.selectbox("Programa", sorted(df2["Programa"].dropna().unique()))

        df3 = df2[df2["Programa"] == prog_sel]

        obj_sel = st.selectbox("Objetivo Específico", sorted(df3["Objetivo"].dropna().unique()))

        df_final = df3[df3["Objetivo"] == obj_sel]

        # -------- RESULTADOS --------
        st.subheader("Entregas")
        entregas = df_final[df_final["Entrega"].notna()]
        st.dataframe(entregas[["Entrega"]], width="stretch")

        st.subheader("Ações")
        acoes = df_final[df_final["Ação"].notna()]
        st.dataframe(acoes[["Ação"]], width="stretch")

        st.subheader("Visão consolidada")
        st.dataframe(df_final, width="stretch")

else:
    st.info("Envie os PDFs para começar.")
