import streamlit as st
import pdfplumber
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Plataforma de Visualização do PPA")

menu = st.sidebar.selectbox(
    "Escolha uma área",
    ["Mapa Intersetorial", "Explorar Dados", "Indicadores"]
)

# -----------------------------
# FUNÇÃO SEGURA PARA LER PDF
# -----------------------------

def ler_pdf(caminho):

    texto = ""

    try:

        with pdfplumber.open(caminho) as pdf:

            for page in pdf.pages:

                t = page.extract_text()

                if t:
                    texto += t + "\n"

        return texto

    except Exception as e:

        st.error(f"Erro ao ler {caminho}")
        st.write(e)

        return ""


# -----------------------------
# CARREGAMENTO DOS ARQUIVOS
# -----------------------------

estrutura_texto = ler_pdf("Anexo-I-PDF.pdf")
indicadores_texto = ler_pdf("Anexo-II-PDF.pdf")

# -----------------------------
# CRIAR DATAFRAME SIMPLES
# -----------------------------

def gerar_dataframe(texto):

    linhas = texto.split("\n")

    dados = []

    for linha in linhas:

        if len(linha) > 20:

            dados.append({"texto": linha})

    return pd.DataFrame(dados)


df = gerar_dataframe(estrutura_texto)

df_ind = gerar_dataframe(indicadores_texto)

# =============================
# MAPA INTERSETORIAL
# =============================

if menu == "Mapa Intersetorial":

    st.header("Mapa Intersetorial do PPA")

    if df.empty:

        st.warning("Não foi possível extrair estrutura do PDF")

    else:

        G = nx.Graph()

        for i in range(min(200, len(df))):

            G.add_node(df.iloc[i]["texto"])

            if i > 0:
                G.add_edge(df.iloc[i-1]["texto"], df.iloc[i]["texto"])

        net = Network(height="750px", width="100%")

        net.from_nx(G)

        net.toggle_physics(True)

        net.save_graph("grafo.html")

        HtmlFile = open("grafo.html", "r", encoding="utf-8")

        components.html(HtmlFile.read(), height=800)


# =============================
# BUSCA
# =============================

elif menu == "Explorar Dados":

    st.header("Busca no PPA")

    busca = st.text_input("Digite palavra-chave")

    if busca:

        resultado = df[df["texto"].str.contains(busca, case=False)]

        st.write(resultado.head(50))


# =============================
# INDICADORES
# =============================

elif menu == "Indicadores":

    st.header("Indicadores do PPA")

    st.write(df_ind.head(200))

    fig = px.histogram(df_ind, x="texto")

    st.plotly_chart(fig)
