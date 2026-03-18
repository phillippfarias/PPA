import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(layout="wide")

st.title("Visualização Intersetorial do PPA")

st.write("Ferramenta de navegação pelas áreas do Plano Plurianual")

# exemplo inicial de estrutura do PPA
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

    G.add_node(eixo, color="#1f77b4")
    G.add_node(tema, color="#2ca02c")
    G.add_node(programa, color="#ff7f0e")

    G.add_edge(eixo, tema)
    G.add_edge(tema, programa)

net = Network(
    height="750px",
    width="100%",
    directed=True,
    bgcolor="#ffffff",
    font_color="black"
)

net.from_nx(G)

net.set_options("""
var options = {
layout: {
hierarchical: {
direction: "LR",
sortMethod: "directed"
}
},
nodes:{
shape:"box",
font:{
size:20
}
},
edges:{
arrows:{
to:{enabled:true}
}
},
physics:false
}
""")

net.save_graph("graph.html")

HtmlFile = open("graph.html","r",encoding="utf-8")
source_code = HtmlFile.read()

components.html(source_code,height=800)
