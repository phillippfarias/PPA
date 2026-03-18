import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(layout="wide")

st.title("Visualização Intersetorial do PPA")
st.write("Ferramenta de navegação pelas áreas do Plano Plurianual")

# dados exemplo
data = {
    "eixo":[
        "Desenvolvimento Social",
        "Desenvolvimento Social",
        "Desenvolvimento Econômico",
        "Desenvolvimento Econômico",
        "Governança"
    ],
    "tema":[
        "Saúde",
        "Educação",
        "Emprego",
        "Inovação",
        "Gestão Pública"
    ],
    "programa":[
        "Saúde Preventiva",
        "Educação Básica",
        "Geração de Emprego",
        "Transformação Digital",
        "Modernização do Estado"
    ]
}

df = pd.DataFrame(data)

G = nx.DiGraph()

for _, row in df.iterrows():

    eixo = row["eixo"]
    tema = row["tema"]
    programa = row["programa"]

    G.add_node(eixo, color="#4F81BD", shape="box")
    G.add_node(tema, color="#9BBB59", shape="box")
    G.add_node(programa, color="#F79646", shape="box")

    G.add_edge(eixo, tema)
    G.add_edge(tema, programa)

net = Network(
    height="750px",
    width="100%",
    directed=True,
    bgcolor="white",
    font_color="black"
)

net.from_nx(G)

# layout horizontal
net.hrepulsion(
    node_distance=200,
    central_gravity=0,
    spring_length=200,
    spring_strength=0.05
)

net.toggle_physics(False)

net.save_graph("graph.html")

with open("graph.html","r",encoding="utf-8") as f:
    source_code = f.read()

components.html(source_code,height=800)
