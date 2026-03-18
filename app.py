import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import networkx as nx
import re

st.set_page_config(layout="wide")

st.title("Observatório do PPA do Ceará")

# -------------------------
# FUNÇÃO DE LEITURA PDF
# -------------------------

@st.cache_data
def extrair_texto_pdf(caminho):

    texto = ""

    with pdfplumber.open(caminho) as pdf:

        for page in pdf.pages:

            conteudo = page.extract_text()

            if conteudo:
                texto += conteudo + "\n"

    return texto


# -------------------------
# PARSER ESTRUTURA
# -------------------------

def parsear_estrutura(texto):

    eixo = None
    tema = None
    programa = None
    entrega = None

    dados = []

    linhas = texto.split("\n")

    for linha in linhas:

        l = linha.strip()

        if re.search("Eixo", l, re.IGNORECASE):
            eixo = l

        elif re.search("Tema", l, re.IGNORECASE):
            tema = l

        elif re.search("Programa", l, re.IGNORECASE):
            programa = l

        elif re.search("Entrega", l, re.IGNORECASE):
            entrega = l

        elif re.search("Ação", l, re.IGNORECASE):

            dados.append(
                {
                    "Eixo": eixo,
                    "Tema": tema,
                    "Programa": programa,
                    "Entrega": entrega,
                    "Acao": l,
                }
            )

    return pd.DataFrame(dados)


# -------------------------
# PARSER INDICADORES
# -------------------------

def parsear_indicadores(texto):

    linhas = texto.split("\n")

    dados = []

    for l in linhas:

        l = l.strip()

        if len(l) > 20:

            dados.append({"Indicador": l})

    return pd.DataFrame(dados)


# -------------------------
# CARREGAMENTO
# -------------------------

with st.spinner("Carregando PPA..."):

    texto1 = extrair_texto_pdf("Anexo-I-PDF.pdf")
    texto2 = extrair_texto_pdf("Anexo-II-PDF.pdf")

    df = parsear_estrutura(texto1)
    df_ind = parsear_indicadores(texto2)


# -------------------------
# MENU
# -------------------------

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Visão Geral",
        "Organograma",
        "Intersetorialidade",
        "Busca",
        "Indicadores"
    ]
)


# -------------------------
# VISÃO GERAL
# -------------------------

if menu == "Visão Geral":

    st.metric("Eixos", df["Eixo"].nunique())
    st.metric("Temas", df["Tema"].nunique())
    st.metric("Programas", df["Programa"].nunique())
    st.metric("Ações", df["Acao"].nunique())

    st.dataframe(df.head(200))


# -------------------------
# ORGANOGRAMA
# -------------------------

elif menu == "Organograma":

    G = nx.DiGraph()

    for _, r in df.iterrows():

        G.add_edge(r["Eixo"], r["Tema"])
        G.add_edge(r["Tema"], r["Programa"])
        G.add_edge(r["Programa"], r["Entrega"])
        G.add_edge(r["Entrega"], r["Acao"])

    pos = nx.spring_layout(G)

    fig = px.scatter()

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        fig.add_scatter(x=[x0, x1], y=[y0, y1], mode="lines")

    for node in G.nodes():

        x, y = pos[node]

        fig.add_scatter(
            x=[x],
            y=[y],
            text=[node],
            mode="markers+text",
            textposition="top center"
        )

    st.plotly_chart(fig, use_container_width=True)


# -------------------------
# INTERSETORIALIDADE
# -------------------------

elif menu == "Intersetorialidade":

    G = nx.Graph()

    for _, r in df.iterrows():

        if pd.notnull(r["Programa"]) and pd.notnull(r["Acao"]):

            G.add_edge(r["Programa"], r["Acao"])

    pos = nx.spring_layout(G)

    fig = px.scatter()

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        fig.add_scatter(x=[x0, x1], y=[y0, y1], mode="lines")

    for node in G.nodes():

        x, y = pos[node]

        fig.add_scatter(
            x=[x],
            y=[y],
            text=[node],
            mode="markers"
        )

    st.plotly_chart(fig, use_container_width=True)


# -------------------------
# BUSCA
# -------------------------

elif menu == "Busca":

    termo = st.text_input("Pesquisar no PPA")

    if termo:

        resultado = df[
            df.apply(lambda r: r.astype(str).str.contains(termo, case=False).any(), axis=1)
        ]

        st.write(len(resultado), "resultados")

        st.dataframe(resultado)


# -------------------------
# INDICADORES
# -------------------------

elif menu == "Indicadores":

    st.dataframe(df_ind.head(200))

    contagem = df_ind["Indicador"].value_counts().head(20)

    fig = px.bar(
        x=contagem.values,
        y=contagem.index,
        orientation="h"
    )

    st.plotly_chart(fig, use_container_width=True)
