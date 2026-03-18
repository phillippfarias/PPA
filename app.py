import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import re

st.set_page_config(layout="wide")

st.title("Observatório do PPA do Ceará")
st.subheader("Visualizador interativo de programas, ações e indicadores")

# ------------------------------------------------------------
# CACHE
# ------------------------------------------------------------

@st.cache_data
def extrair_texto_pdf(caminho):

    texto = ""

    with pdfplumber.open(caminho) as pdf:

        for page in pdf.pages:

            t = page.extract_text()

            if t:
                texto += t + "\n"

    return texto


# ------------------------------------------------------------
# PARSER DA ESTRUTURA DO PPA
# ------------------------------------------------------------

def parsear_estrutura(texto):

    linhas = texto.split("\n")

    eixo = None
    tema = None
    programa = None
    entrega = None

    dados = []

    for l in linhas:

        l = l.strip()

        if re.search(r"Eixo", l, re.IGNORECASE):
            eixo = l

        elif re.search(r"Tema", l, re.IGNORECASE):
            tema = l

        elif re.search(r"Programa", l, re.IGNORECASE):
            programa = l

        elif re.search(r"Entrega", l, re.IGNORECASE):
            entrega = l

        elif re.search(r"Ação", l, re.IGNORECASE):

            acao = l

            dados.append(
                {
                    "Eixo": eixo,
                    "Tema": tema,
                    "Programa": programa,
                    "Entrega": entrega,
                    "Acao": acao,
                }
            )

    df = pd.DataFrame(dados)

    return df


# ------------------------------------------------------------
# PARSER DOS INDICADORES
# ------------------------------------------------------------

def parsear_indicadores(texto):

    linhas = texto.split("\n")

    dados = []

    for l in linhas:

        l = l.strip()

        if len(l) > 20:

            dados.append({"Indicador": l})

    return pd.DataFrame(dados)


# ------------------------------------------------------------
# CARREGAMENTO
# ------------------------------------------------------------

with st.spinner("Carregando dados do PPA..."):

    texto_estrutura = extrair_texto_pdf("Anexo-I-PDF.pdf")
    texto_indicadores = extrair_texto_pdf("Anexo-II-PDF.pdf")

    df = parsear_estrutura(texto_estrutura)
    df_ind = parsear_indicadores(texto_indicadores)

# ------------------------------------------------------------
# MENU
# ------------------------------------------------------------

menu = st.sidebar.selectbox(
    "Navegação",
    [
        "Visão Geral",
        "Organograma do PPA",
        "Intersetorialidade",
        "Buscar no PPA",
        "Indicadores"
    ]
)

# ------------------------------------------------------------
# VISÃO GERAL
# ------------------------------------------------------------

if menu == "Visão Geral":

    st.metric("Eixos", df["Eixo"].nunique())
    st.metric("Temas", df["Tema"].nunique())
    st.metric("Programas", df["Programa"].nunique())
    st.metric("Ações", df["Acao"].nunique())

    st.write("Estrutura do PPA")

    st.dataframe(df.head(200))


# ------------------------------------------------------------
# ORGANOGRAMA
# ------------------------------------------------------------

elif menu == "Organograma do PPA":

    st.header("Organograma Hierárquico do PPA")

    G = nx.DiGraph()

    for _, r in df.iterrows():

        G.add_edge(r["Eixo"], r["Tema"])
        G.add_edge(r["Tema"], r["Programa"])
        G.add_edge(r["Programa"], r["Entrega"])
        G.add_edge(r["Entrega"], r["Acao"])

    pos = nx.spring_layout(G)

    edge_x = []
    edge_y = []

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines"
    )

    node_x = []
    node_y = []
    node_text = []

    for node in G.nodes():

        x, y = pos[node]

        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=node_text,
        mode="markers+text",
        textposition="top center"
    )

    fig = go.Figure(data=[edge_trace, node_trace])

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# INTERSETORIALIDADE
# ------------------------------------------------------------

elif menu == "Intersetorialidade":

    st.header("Mapa de Intersetorialidade")

    G = nx.Graph()

    for _, r in df.iterrows():

        if pd.notnull(r["Programa"]) and pd.notnull(r["Acao"]):

            G.add_edge(r["Programa"], r["Acao"])

    pos = nx.spring_layout(G)

    edge_x = []
    edge_y = []

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines"
    )

    node_x = []
    node_y = []
    node_text = []

    for node in G.nodes():

        x, y = pos[node]

        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=node_text,
        mode="markers",
        marker=dict(size=8)
    )

    fig = go.Figure(data=[edge_trace, node_trace])

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# BUSCA
# ------------------------------------------------------------

elif menu == "Buscar no PPA":

    st.header("Busca no PPA")

    termo = st.text_input("Digite um termo")

    if termo:

        resultado = df[
            df.apply(lambda row: row.astype(str).str.contains(termo, case=False).any(), axis=1)
        ]

        st.write(f"{len(resultado)} resultados")

        st.dataframe(resultado)


# ------------------------------------------------------------
# INDICADORES
# ------------------------------------------------------------

elif menu == "Indicadores":

    st.header("Painel de Indicadores")

    st.dataframe(df_ind.head(200))

    contagem = df_ind["Indicador"].value_counts().head(15)

    fig = px.bar(
        x=contagem.values,
        y=contagem.index,
        orientation="h"
    )

    st.plotly_chart(fig, use_container_width=True)
