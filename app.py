import streamlit as st
import pdfplumber
import pandas as pd
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(layout="wide")

st.title("Visualização Intersetorial do PPA")

st.sidebar.header("Carregar arquivos")

pdf1 = st.sidebar.file_uploader("Estrutura do PPA (Anexo I)", type="pdf")
pdf2 = st.sidebar.file_uploader("Indicadores (Anexo II)", type="pdf")

menu = st.sidebar.selectbox(
    "Escolha a visualização",
    [
        "Mapa Intersetorial",
        "Buscar no PPA",
        "Indicadores"
    ]
)

# -------------------------------------------------

def ler_pdf(arquivo):

    texto = ""

    with pdfplumber.open(arquivo) as pdf:

        for page in pdf.pages:

            conteudo = page.extract_text()

            if conteudo:
                texto += conteudo + "\n"

    return texto

# -------------------------------------------------

def gerar_dataframe(texto):

    linhas = texto.split("\n")

    dados = []

    for linha in linhas:

        linha = linha.strip()

        if len(linha) > 15:
            dados.append({"texto": linha})

    return pd.DataFrame(dados)

# -------------------------------------------------

if menu == "Mapa Intersetorial":

    if pdf1 is None:

        st.warning("Envie o PDF do Anexo I na barra lateral.")

    else:

        texto = ler_pdf(pdf1)
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
            textposition="top center",
            marker=dict(size=10)
        )

        fig = go.Figure(data=[edge_trace, node_trace])

        st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------

elif menu == "Buscar no PPA":

    if pdf1 is None:

        st.warning("Envie o PDF do Anexo I.")

    else:

        texto = ler_pdf(pdf1)
        df = gerar_dataframe(texto)

        busca = st.text_input("Digite palavra-chave")

        if busca:

            resultado = df[df["texto"].str.contains(busca, case=False)]

            st.write(f"{len(resultado)} resultados")

            st.dataframe(resultado.head(200))

# -------------------------------------------------

elif menu == "Indicadores":

    if pdf2 is None:

        st.warning("Envie o PDF do Anexo II.")

    else:

        texto = ler_pdf(pdf2)
        df = gerar_dataframe(texto)

        st.dataframe(df.head(200))

        contagem = df["texto"].value_counts().head(20)

        fig = go.Figure()

        fig.add_bar(
            x=contagem.index,
            y=contagem.values
        )

        st.plotly_chart(fig, use_container_width=True)
