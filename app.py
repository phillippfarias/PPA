import streamlit as st
import pdfplumber
import pandas as pd
import re
import networkx as nx
from pyvis.network import Network
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("Plataforma de Visualização do PPA")

menu = st.sidebar.radio(
    "Navegação",
    ["Mapa Intersetorial", "Busca de Programas", "Indicadores do PPA"]
)

# -------------------------
# LEITURA DOS PDFs
# -------------------------

@st.cache_data
def extrair_texto(pdf):

    texto = ""

    with pdfplumber.open(pdf) as pdf_file:
        for page in pdf_file.pages:
            t = page.extract_text()
            if t:
                texto += t + "\n"

    return texto


estrutura_texto = extrair_texto("Anexo-I-PDF.pdf")
indicadores_texto = extrair_texto("Anexo-II-PDF.pdf")


# -------------------------
# EXTRAÇÃO DA ESTRUTURA
# -------------------------

@st.cache_data
def extrair_estrutura(texto):

    linhas = texto.split("\n")

    eixo = None
    tema = None
    programa = None
    entrega = None

    dados = []

    for linha in linhas:

        linha = linha.strip()

        if linha.startswith("Eixo"):
            eixo = linha

        elif linha.startswith("Tema"):
            tema = linha

        elif linha.startswith("Programa"):
            programa = linha

        elif linha.startswith("Entrega"):
            entrega = linha

        elif re.match(r"\d{4,}", linha):

            acao = linha

            sigla = re.findall(r"- ([A-Z]{3,5})", acao)

            secretaria = sigla[-1] if sigla else None

            dados.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Entrega": entrega,
                "Acao": acao,
                "Secretaria": secretaria
            })

    return pd.DataFrame(dados)


df_estrutura = extrair_estrutura(estrutura_texto)

# -------------------------
# EXTRAÇÃO DOS INDICADORES
# -------------------------

@st.cache_data
def extrair_indicadores(texto):

    linhas = texto.split("\n")

    dados = []

    for linha in linhas:

        if "Indicador" in linha or "Meta" in linha:

            dados.append({"texto": linha})

    return pd.DataFrame(dados)


df_indicadores = extrair_indicadores(indicadores_texto)

# =========================
# MAPA INTERSETORIAL
# =========================

if menu == "Mapa Intersetorial":

    st.header("Mapa Intersetorial do PPA")

    secretarias = df_estrutura["Secretaria"].dropna().unique()

    filtro = st.multiselect(
        "Filtrar por secretaria",
        secretarias,
        default=secretarias
    )

    df = df_estrutura[df_estrutura["Secretaria"].isin(filtro)]

    G = nx.DiGraph()

    for _, row in df.iterrows():

        eixo = row["Eixo"]
        tema = row["Tema"]
        programa = row["Programa"]
        entrega = row["Entrega"]
        acao = row["Acao"]

        if eixo:
            G.add_node(eixo, color="#1f77b4")

        if tema:
            G.add_node(tema, color="#2ca02c")
            G.add_edge(eixo, tema)

        if programa:
            G.add_node(programa, color="#ff7f0e")
            G.add_edge(tema, programa)

        if entrega:
            G.add_node(entrega, color="#9467bd")
            G.add_edge(programa, entrega)

        if acao:
            G.add_node(acao, color="#d62728")
            G.add_edge(entrega, acao)

    net = Network(height="800px", width="100%", directed=True)

    net.from_nx(G)

    net.toggle_physics(False)

    net.save_graph("grafo.html")

    HtmlFile = open("grafo.html", "r", encoding="utf-8")
    components.html(HtmlFile.read(), height=850)

# =========================
# BUSCA DE PROGRAMAS
# =========================

elif menu == "Busca de Programas":

    st.header("Busca no PPA")

    busca = st.text_input("Digite o nome do programa ou ação")

    if busca:

        resultado = df_estrutura[
            df_estrutura["Programa"].str.contains(busca, case=False, na=False) |
            df_estrutura["Acao"].str.contains(busca, case=False, na=False)
        ]

        st.write(resultado)

# =========================
# INDICADORES
# =========================

elif menu == "Indicadores do PPA":

    st.header("Indicadores do PPA")

    st.write("Indicadores extraídos do Anexo II")

    st.write(df_indicadores)

    contagem = df_indicadores.shape[0]

    fig = px.bar(
        x=["Indicadores identificados"],
        y=[contagem],
        labels={"x": "", "y": "Quantidade"}
    )

    st.plotly_chart(fig)
