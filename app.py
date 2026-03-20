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


# -------- PARSER --------
def parse_ppa(df):

    estrutura = []

    eixo = tema = programa = objetivo = None

    for _, row in df.iterrows():
        line = row["text"].strip()
        up = line.upper()

        if re.match(r"^\d+\s*-\s*", line):
            eixo = line
            tema = programa = objetivo = None

        elif re.match(r"^\d+\.\d+\s*-", line):
            tema = line
            programa = objetivo = None

        elif re.match(r"^\d{3,}\s*-", line):
            programa = line
            objetivo = None

        elif "OBJETIVO ESPECÍFICO" in up:
            objetivo = line

        elif "ENTREGA" in up or up.startswith("BENEFÍCIO"):
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo": objetivo,
                "Entrega": line,
                "Ação": None
            })

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


# -------- UI --------
st.title("Mapa do PPA")

files = st.file_uploader("Envie os PDFs", type=["pdf"], accept_multiple_files=True)

if files:

    df_texto = extract_text(files)
    df = parse_ppa(df_texto)

    if df.empty:
        st.error("Nada foi identificado. Precisamos ajustar o parser.")
    else:
        eixo = st.selectbox("Eixo", df["Eixo"].dropna().unique())
        df1 = df[df["Eixo"] == eixo]

        tema = st.selectbox("Tema", df1["Tema"].dropna().unique())
        df2 = df1[df1["Tema"] == tema]

        prog = st.selectbox("Programa", df2["Programa"].dropna().unique())
        df3 = df2[df2["Programa"] == prog]

        obj = st.selectbox("Objetivo", df3["Objetivo"].dropna().unique())
        df_final = df3[df3["Objetivo"] == obj]

        st.subheader("Entregas")
        st.dataframe(df_final[df_final["Entrega"].notna()][["Entrega"]])

        st.subheader("Ações")
        st.dataframe(df_final[df_final["Ação"].notna()][["Ação"]])

else:
    st.info("Envie os PDFs.")
