# app.py
import streamlit as st
from pypdf import PdfReader
import pandas as pd
import re

st.set_page_config(layout="wide")

# -------- PDF PROCESSING --------

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        try:
            content = page.extract_text()
            if content:
                text += content + "\n"
        except:
            pass
    return text

# -------- PARSER SIMPLES DO PPA --------

def parse_ppa_structure(text):
    estrutura = []

    eixo = None
    tema = None
    programa = None
    objetivo = None

    lines = text.split("\n")

    for line in lines:
        line = line.strip()

        # Ajuste esses padrões conforme o PDF real
        if re.search(r"Eixo", line, re.IGNORECASE):
            eixo = line
            tema = programa = objetivo = None

        elif re.search(r"Tema", line, re.IGNORECASE):
            tema = line
            programa = objetivo = None

        elif re.search(r"Programa", line, re.IGNORECASE):
            programa = line
            objetivo = None

        elif re.search(r"Objetivo", line, re.IGNORECASE):
            objetivo = line

        elif re.search(r"Entrega|Ação", line, re.IGNORECASE):
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo": objetivo,
                "Entrega/Ação": line
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

    full_text = ""

    with st.spinner("Processando PDFs..."):
        for file in uploaded_files:
            full_text += extract_text_from_pdf(file)

    df = parse_ppa_structure(full_text)

    if df.empty:
        st.warning("Não foi possível identificar a estrutura automaticamente. Precisamos ajustar o parser.")

    else:
        st.success("Estrutura carregada!")

        # -------- NAVEGAÇÃO HIERÁRQUICA --------
        eixo_sel = st.selectbox("Eixo", sorted(df["Eixo"].dropna().unique()))

        df_tema = df[df["Eixo"] == eixo_sel]
        tema_sel = st.selectbox("Tema", sorted(df_tema["Tema"].dropna().unique()))

        df_prog = df_tema[df_tema["Tema"] == tema_sel]
        prog_sel = st.selectbox("Programa", sorted(df_prog["Programa"].dropna().unique()))

        df_obj = df_prog[df_prog["Programa"] == prog_sel]
        obj_sel = st.selectbox("Objetivo", sorted(df_obj["Objetivo"].dropna().unique()))

        df_final = df_obj[df_obj["Objetivo"] == obj_sel]

        st.subheader("Entregas / Ações")
        st.dataframe(df_final[["Entrega/Ação"]])

        # -------- INDICADORES (placeholder) --------
        st.subheader("Indicadores relacionados (protótipo)")
        st.info("Aqui você poderá conectar os indicadores a cada nível.")

else:
    st.info("Envie os PDFs para começar.")

# -------- PRÓXIMOS PASSOS --------
st.markdown("""
### Evoluções recomendadas:
- Refinar parser com padrões reais do PPA
- Conectar indicadores automaticamente
- Criar visualização em árvore (tree graph)
- Permitir exportação dos dados
""")


# requirements.txt
# ----------------
# streamlit
# pypdf
# pandas
