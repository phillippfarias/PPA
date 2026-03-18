import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import networkx as nx
import re

st.set_page_config(layout="wide")

st.title("Observatório do PPA do Ceará")
st.write("Visualizador interativo do Plano Plurianual")

# ------------------------------
# Função para extrair texto
# ------------------------------

@st.cache_data
def extrair_texto_pdf(caminho):

    texto = ""

    with pdfplumber.open(caminho) as pdf:

        for page in pdf.pages:

            t = page.extract_text()

            if t:
                texto += t + "\n"

    return texto


# ------------------------------
# Parser da estrutura
# ------------------------------

def parsear_estrutura(texto):

    eixo = None
    tema = None
    programa = None
    entrega = None

    dados = []

    for linha in texto.split("\n"):

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

            dados.append({
                "Eixo": eixo,
                "Tema": tema,
                "Programa": programa,
                "Entrega": entrega,
                "Acao": l
            })

    return pd.DataFrame(dados)


# ------------------------------
# Parser indicadores
# ------------------------------

def parsear_indicadores(texto):

    dados = []

    for linha in texto.split("\n"):

        l = linha.strip()

        if len(l) > 20:
            dados.append({"Indicador": l})

    return pd.DataFrame(dados)


# ------------------------------
# Botão para carregar dados
# ------------------------------

if "dados_carregados" not in st.session_state:
    st.session_state.dados_carregados = False

if st.button("Carregar dados do PPA"):

    with st.spinner("Lendo PDFs..."):

        texto1 = extrair_texto_pdf("Anexo-I-PDF.pdf")
        texto2 = extrair_texto_pdf("Anexo-II-PDF.pdf")

        st.session_state.df = parsear_estrutura(texto1)
        st.session_state.df_ind = parsear_indicadores(texto2)

        st.session_state.dados_carregados = True

# ------------------------------

if not st.session_state.dados_carregados:

    st.info("Clique em 'Carregar dados do PPA' para iniciar.")

else:

    df = st.session_state.df
    df_ind = st.session_state.df_ind

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

    # --------------------------

    if menu == "Visão Geral":

        st.metric("Eixos", df["Eixo"].nunique())
        st.metric("Temas", df["Tema"].nunique())
        st.metric("Programas", df["Programa"].nunique())
        st.metric("Ações", df["Acao"].nunique())

        st.dataframe(df.head(200))

    # --------------------------

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

    # --------------------------

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

            fig.add_scatter(x=[x], y=[y], mode="markers")

        st.plotly_chart(fig, use_container_width=True)

    # --------------------------

    elif menu == "Busca":

        termo = st.text_input("Pesquisar no PPA")

        if termo:

            resultado = df[
                df.apply(lambda r: r.astype(str).str.contains(termo, case=False).any(), axis=1)
            ]

            st.write(len(resultado), "resultados")

            st.dataframe(resultado)

    # --------------------------

    elif menu == "Indicadores":

        st.dataframe(df_ind.head(200))

        contagem = df_ind["Indicador"].value_counts().head(20)

        fig = px.bar(
            x=contagem.values,
            y=contagem.index,
            orientation="h"
        )

        st.plotly_chart(fig, use_container_width=True)
