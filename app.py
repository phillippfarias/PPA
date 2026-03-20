import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(layout="wide")

# -------- EXTRAÇÃO --------
def extract_structured_text(files):
    data = []

    for file in files:
        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()

                if text:
                    lines = text.split("\n")
                    for line in lines:
                        data.append({
                            "page": page_num + 1,
                            "text": line.strip()
                        })

    return pd.DataFrame(data)


# -------- PARSER DO PPA --------
def parse_ppa(df_texto):

    estrutura = []

    eixo = tema = programa = objetivo = None

    for _, row in df_texto.iterrows():
        line = row["text"]

        # Normaliza texto
        line_upper = line.upper()

        # -------- IDENTIFICAÇÃO DOS NÍVEIS --------

        if re.match(r"^EIXO", line_upper):
            eixo = line
            tema = programa = objetivo = None

        elif re.match(r"^TEMA", line_upper):
            tema = line
            programa = objetivo = None

        elif re.match(r"^PROGRAMA", line_upper):
            programa = line
            objetivo = None

        elif re.match(r"OBJETIVO", line_upper):
            objetivo = line

        elif re.match(r"ENTREGA|AÇÃO", line_upper):
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo Específico": objetivo,
                "Entrega/Ação": line,
                "Indicador": None
            })

        elif re.match(r"INDICADOR", line_upper):
            estrutura.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Objetivo Específico": objetivo,
                "Entrega/Ação": None,
                "Indicador": line
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

    with st.spinner("Extraindo dados do PDF..."):
        df_texto = extract_structured_text(uploaded_files)

    with st.spinner("Estruturando o PPA..."):
        df = parse_ppa(df_texto)

    if df.empty:
        st.error("Não foi possível identificar a estrutura. Precisamos ajustar o parser.")
    else:
        st.success("PPA estruturado com sucesso!")

        # -------- NAVEGAÇÃO --------

        eixo_sel = st.selectbox(
            "Eixo",
            sorted(df["Eixo"].dropna().unique())
        )

        df1 = df[df["Eixo"] == eixo_sel]

        tema_sel = st.selectbox(
            "Tema",
            sorted(df1["Tema"].dropna().unique())
        )

        df2 = df1[df1["Tema"] == tema_sel]

        prog_sel = st.selectbox(
            "Programa",
            sorted(df2["Programa"].dropna().unique())
        )

        df3 = df2[df2["Programa"] == prog_sel]

        obj_sel = st.selectbox(
            "Objetivo Específico",
            sorted(df3["Objetivo Específico"].dropna().unique())
        )

        df_final = df3[df3["Objetivo Específico"] == obj_sel]

        # -------- RESULTADOS --------

        st.subheader("Entregas / Ações")
        entregas = df_final[df_final["Entrega/Ação"].notna()]
        st.dataframe(entregas[["Entrega/Ação"]], use_container_width=True)

        st.subheader("Indicadores relacionados")
        indicadores = df_final[df_final["Indicador"].notna()]
        st.dataframe(indicadores[["Indicador"]], use_container_width=True)

        # -------- VISÃO CONSOLIDADA --------

        st.subheader("Visão consolidada")
        st.dataframe(df_final, use_container_width=True)

else:
    st.info("Envie os PDFs para começar.")


# -------- INFO FINAL --------
st.markdown("""
### O que essa versão já resolve:
- Estrutura real do PPA (hierarquia completa)
- Navegação por níveis
- Separação de entregas e indicadores

### Próximos upgrades possíveis:
- Árvore interativa (expandir/recolher)
- Mapa de intersetorialidade entre programas
- Exportação para Excel
- Dashboard analítico
""")
