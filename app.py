import streamlit as st
import pdfplumber
import pandas as pd
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(layout="wide")

st.title("Visualização Intersetorial do PPA")
st.write("Ferramenta de navegação pelas áreas do Plano Plurianual")

menu = st.sidebar.selectbox(
    "Escolha a visualização",
    [
        "Mapa Intersetorial",
        "Buscar no PPA",
        "Indicadores"
    ]
)

# -------------------------------------------------
# CACHE PARA NÃO REPROCESSAR PDF TODA VEZ
# -------------------------------------------------

@st.cache_data
def ler_pdf(caminho):

    texto = ""

    with pdfplumber.open(caminho) as pdf:

        for page in pdf.pages:

            conteudo = page.extract_text()

            if conteudo:
                texto += conteudo + "\n"

    return texto


@st.cache_data
def gerar_dataframe(texto):

    linhas = texto.split("\n")

    dados = []

    for linha in linhas:

        linha = linha.strip()

        if len(linha) > 15:

            dados.append({"texto": linha})

    return pd.DataFrame(dados)


# -------------------------------------------------
# CARREGAMENTO SOB DEMANDA
# -------------------------------------------------

if menu == "Mapa Intersetorial":

    st.header("Mapa Intersetorial")

    texto = ler_pdf("Anexo-I-PDF.pdf")
    df = gerar_dataframe(texto)

    limite = min(120, len(df))

    G = nx.Graph()

    for i in range(limite):

        node = df.iloc[i]["texto"]

        G.add_node(node)

        if i > 0:

            prev = df.iloc[i-1]["texto"]

            G.add_edge(prev, node)

    pos = nx.spring_layout(G)

    edge_x = []
    edge_y = []

    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)

        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

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
        textposition="top center",
        marker=dict(size=10)
    )

    fig = go.Figure(data=[edge_trace, node_trace])

    st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------

elif menu == "Buscar no PPA":

    st.header("Buscar no PPA")

    texto = ler_pdf("Anexo-I-PDF.pdf")
    df = gerar_dataframe(texto)

    busca = st.text_input("Digite palavra-chave")

    if busca:

        resultado = df[df["texto"].str.contains(busca, case=False)]

        st.write(f"{len(resultado)} resultados")

        st.dataframe(resultado.head(200))


# -------------------------------------------------

elif menu == "Indicadores":

    st.header("Indicadores")

    texto = ler_pdf("Anexo-II-PDF.pdf")
    df = gerar_dataframe(texto)

    st.dataframe(df.head(200))

    contagem = df["texto"].value_counts().head(20)

    fig = go.Figure()

    fig.add_bar(
        x=contagem.index,
        y=contagem.values
    )

    st.plotly_chart(fig, use_container_width=True)
