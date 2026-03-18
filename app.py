import streamlit as st
import pdfplumber
import pandas as pd
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(layout="wide")

st.title("Visualização Intersetorial do PPA")
st.subheader("Ferramenta de navegação pelas áreas do Plano Plurianual")

# -----------------------------
# MENU
# -----------------------------

menu = st.sidebar.selectbox(
    "Escolha a visualização",
    [
        "Mapa Intersetorial",
        "Explorar Estrutura",
        "Indicadores"
    ]
)

# -----------------------------
# FUNÇÃO LEITURA PDF
# -----------------------------

def ler_pdf(arquivo):

    texto = ""

    try:
        with pdfplumber.open(arquivo) as pdf:

            for page in pdf.pages:

                conteudo = page.extract_text()

                if conteudo:
                    texto += conteudo + "\n"

    except:
        st.warning(f"Erro ao ler {arquivo}")

    return texto


# -----------------------------
# TRANSFORMAR TEXTO EM DATAFRAME
# -----------------------------

def gerar_dataframe(texto):

    linhas = texto.split("\n")

    dados = []

    for linha in linhas:

        if len(linha.strip()) > 20:

            dados.append({"texto": linha})

    return pd.DataFrame(dados)


# -----------------------------
# CARREGAR DADOS
# -----------------------------

with st.spinner("Carregando PPA..."):

    estrutura_texto = ler_pdf("Anexo-I-PDF.pdf")
    indicadores_texto = ler_pdf("Anexo-II-PDF.pdf")

    df = gerar_dataframe(estrutura_texto)
    df_ind = gerar_dataframe(indicadores_texto)


# ====================================================
# MAPA INTERSETORIAL
# ====================================================

if menu == "Mapa Intersetorial":

    st.header("Mapa Intersetorial do PPA")

    limite = min(150, len(df))

    G = nx.Graph()

    for i in range(limite):

        node = df.iloc[i]["texto"]

        G.add_node(node)

        if i > 0:
            G.add_edge(df.iloc[i-1]["texto"], node)

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
        line=dict(width=1),
        hoverinfo='none',
        mode='lines'
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
        mode='markers+text',
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            size=10
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest'
        )
    )

    st.plotly_chart(fig, use_container_width=True)


# ====================================================
# BUSCA NA ESTRUTURA
# ====================================================

elif menu == "Explorar Estrutura":

    st.header("Busca na Estrutura do PPA")

    busca = st.text_input("Buscar programa, ação ou tema")

    if busca:

        resultado = df[df["texto"].str.contains(busca, case=False)]

        st.dataframe(resultado.head(200))

    else:

        st.write("Digite um termo para pesquisar.")


# ====================================================
# INDICADORES
# ====================================================

elif menu == "Indicadores":

    st.header("Indicadores do PPA")

    st.dataframe(df_ind.head(200))

    contagem = df_ind["texto"].value_counts().head(20)

    fig = go.Figure()

    fig.add_bar(
        x=contagem.index,
        y=contagem.values
    )

    st.plotly_chart(fig, use_container_width=True)
