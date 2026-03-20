import streamlit as st
from pypdf import PdfReader
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

st.set_page_config(layout="wide")

# -------- LOAD MODEL --------
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# -------- PDF PROCESSING --------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        try:
            content = page.extract_text()
            if content:
                text += content + "\n"
        except:
            pass
    return text


def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def build_vector_store(chunks):
    embeddings = model.encode(chunks, show_progress_bar=False)
    embeddings = np.array(embeddings).astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    return index, embeddings


# -------- UI --------
st.title("Visualizador de Intersetorialidade do PPA")

uploaded_files = st.file_uploader(
    "Envie os PDFs do PPA",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    all_chunks = []

    with st.spinner("Processando PDFs... (pode levar alguns minutos)"):
        for file in uploaded_files:
            text = extract_text_from_pdf(file)
            chunks = chunk_text(text)
            all_chunks.extend(chunks)

        index, embeddings = build_vector_store(all_chunks)

    st.success(f"{len(all_chunks)} trechos processados")

    # -------- BUSCA --------
    query = st.text_input("Buscar termos (ex: programa, indicador, eixo...)")

    if query:
        query_vec = model.encode([query])
        query_vec = np.array(query_vec).astype("float32")

        D, I = index.search(query_vec, k=5)

        st.subheader("Resultados mais relevantes")
        for i in I[0]:
            st.write(all_chunks[i])
            st.markdown("---")

    # -------- GRAFO --------
    st.subheader("Visualização de Relações (Protótipo)")

    max_nodes = min(50, len(all_chunks))
    sample_nodes = all_chunks[:max_nodes]

    G = nx.Graph()

    for i, chunk in enumerate(sample_nodes):
        G.add_node(i, label=chunk[:80])

    for i in range(len(sample_nodes)):
        for j in range(i + 1, len(sample_nodes)):
            sim = np.dot(embeddings[i], embeddings[j])
            if sim > 0.7:
                G.add_edge(i, j)

    pos = nx.spring_layout(G, seed=42)

    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    texts = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        texts.append(G.nodes[node]['label'])

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        hovertext=texts,
        hoverinfo="text",
        marker=dict(size=10)
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Envie os PDFs para começar.")

# -------- DICAS --------
st.markdown("""
### Próximos passos recomendados:
- Estruturar automaticamente os níveis do PPA (eixo, tema, programa...)
- Criar banco de dados estruturado
- Melhorar o grafo com hierarquia real (não só similaridade)
""")
