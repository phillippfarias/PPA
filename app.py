import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(layout="wide")

# -------- EXTRAÇÃO --------
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


# -------- PARSER AJUSTADO AO SEU PDF --------
def parse_ppa(df):

    estrutura = []

    eixo = tema = programa = objetivo = None

    for _, row in df.iterrows():
        line = row["text"]

        # remove espaços extras
        line_clean = line.strip()

        # -------- EIXO --------
        if re.match(r"^\\d+\\s*-\\s*O CEARÁ", line_clean.upper()):
            eixo = line_clean
            tema = programa = objetivo = None

        # -------- TEMA --------
        elif re.match(r"^\\d+\\.\\d+\\s*-", line_clean):
            tema = line_clean
            programa = objetivo = None

        # -------- PROGRAMA --------
        elif re.match(r"^\\d{3,}\\s*-", line_clean):
            programa = line_clean
            objetivo = None

        # -------- OBJETIVO --------
        elif "OBJETIVO ESPECÍFICO" in line_clean.upper():
            objetivo = line_clean

        # -------- ENTREGA --------
        elif line_clean.upper().startswith("BENEFÍCIO") or "ENTREGA" in line_clean.upper():
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo": objetivo,
                "Entrega": line_clean,
                "Indicador": None
            })

        # -------- AÇÃO --------
        elif re.match(r"^\\d{4,}\\s*-", line_clean):
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo": objetivo,
                "Entrega": None,
                "Indicador": None,
                "Ação": line_clean
            })

        # -------- INDICADOR (se existir no outro PDF) --------
        elif "INDICADOR" in line_clean.upper():
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo": objetivo,
                "Entrega": None,
                "Indicador": line_clean
            })

    return pd.DataFrame(estrutura)


# -------- UI --------
st.title("Mapa Interativo do PPA")

uploaded_files = st.file_uploader(
    "Envie os PDFs do PPA",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    with st.spinner("Extraindo texto..."):
        df_texto = extract_text(uploaded_files)

    with st.spinner("Estruturando PPA..."):
        df = parse_ppa(df_texto)

    if df.empty:
        st.error("Parser não conseguiu identificar a estrutura.")
    else:
        st.success("PPA estruturado!")

        # -------- FILTROS --------
        eixo_sel = st.selectbox("Eixo", df["Eixo"].dropna().unique())

        df1 = df[df["Eixo"] == eixo_sel]

        tema_sel = st.selectbox("Tema", df1["Tema"].dropna().unique())

        df2 = df1[df1["Tema"] == tema_sel]

        prog_sel = st.selectbox("Programa", df2["Programa"].dropna().unique())

        df3 = df2[df2["Programa"] == prog_sel]

        obj_sel = st.selectbox("Objetivo", df3["Objetivo"].dropna().unique())

        df_final = df3[df3["Objetivo"] == obj_sel]

        # -------- SAÍDA --------
        st.subheader("Entregas")
        st.dataframe(df_final[df_final["Entrega"].notna()][["Entrega"]], width="stretch")

        st.subheader("Ações")
        if "Ação" in df_final.columns:
            st.dataframe(df_final[df_final["Ação"].notna()][["Ação"]], width="stretch")

        st.subheader("Indicadores")
        st.dataframe(df_final[df_final["Indicador"].notna()][["Indicador"]], width="stretch")

        st.subheader("Base completa")
        st.dataframe(df_final, width="stretch")

else:
    st.info("Envie os PDFs para começar.")
