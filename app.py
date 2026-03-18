import streamlit as st
import pdfplumber
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Visualização Intersetorial do PPA")
st.subheader("Ferramenta de navegação pelas áreas do Plano Plurianual")

# -----------------------------
# MENU LATERAL
# -----------------------------

menu = st.sidebar.selectbox(
    "Escolha a visualização",
    [
        "Mapa Intersetorial",
        "Explorar Estrutura do PPA",
        "Indicadores"
    ]
)

# -----------------------------
# FUNÇÃO PARA LER PDF
# -----------------------------

def ler_pdf(caminho):

    texto = ""

    try:

        with pdfplumber.open(caminho) as pdf:

            for page in pdf.pages:

                conteudo = page.extract_text()

                if conteudo:
                    texto += conteudo + "\n"

    except Exception as e:

        st.error(f"Erro ao ler arquivo {caminho}")
        st.write(e)

    return texto


# -----------------------------
# FUNÇÃO PARA CRIAR DATAFRAME
# -----------------------------

def gerar_dataframe(texto):

    linhas = texto.split("\n")

    dados = []

    for linha in linhas:

        if len(linha.strip()) > 15:

            dados.append({"texto": linha})

    return pd.DataFrame(dados)


# -----------------------------
# CARREGAR DADOS
# -----------------------------

with st.spinner("Carregando dados do PPA..."):

    estrutura_texto = ler_pdf("Anexo-I-PDF.pdf")
    indicadores_texto = ler_pdf("Anexo-II-PDF.pdf")

    df = gerar_dataframe(estrutura_texto)
    df_ind = gerar_dataframe(indicadores_texto)


# ====================================================
# MAPA INTERSETORIAL
# ====================================================

if menu == "Mapa Intersetorial":

    st.header("Mapa Intersetorial do PPA")

    if df.empty:

        st.warning("Não foi possível extrair estrutura do PDF")

    else:

        limite = min(250, len(df))

        G = nx.Graph()

        for i in range(limite):

            node = df.iloc[i]["texto"]

            G.add_node(node)

            if i > 0:

                anterior = df.iloc[i - 1]["texto"]

                G.add_edge(anterior, node)

        net = Network(
            height="750px",
            width="100%",
            bgcolor="white",
            font_color="black"
        )

        net.from_nx(G)

        net.toggle_physics(True)

        html = net.generate_html()

        components.html(html, height=800)


# ====================================================
# BUSCA NA ESTRUTURA DO PPA
# ====================================================

elif menu == "Explorar Estrutura do PPA":

    st.header("Busca na Estrutura do PPA")

    busca = st.text_input("Digite palavra-chave")

    if busca:

        resultado = df[df["texto"].str.contains(busca, case=False)]

        st.write("Resultados encontrados:")

        st.dataframe(resultado.head(100))

    else:

        st.write("Digite um termo para iniciar a busca.")


# ====================================================
# INDICADORES
# ====================================================

elif menu == "Indicadores":

    st.header("Indicadores do PPA")

    st.write("Pré-visualização dos dados extraídos:")

    st.dataframe(df_ind.head(200))

    st.write("Distribuição de indicadores:")

    fig = px.histogram(
        df_ind,
        x="texto",
        title="Distribuição textual dos indicadores"
    )

    st.plotly_chart(fig)
