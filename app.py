import streamlit as st
import pandas as pd
import numpy as np
from drive_utils import list_excel_files, read_excel_from_drive
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Pedidos IA", page_icon="🤖", layout="wide")

# --- ESTADO DE SESIÓN ---
if 'pedido' not in st.session_state:
    st.session_state.pedido = []
if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = None

# --- IDS DE DRIVE ---
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrIPeCaN2xwOAf5Bue" 
FOLDER_LISTAS   = "1COsdgql81C20ePt41qTagXgMZ5RnmnGu"   

# --- CARGA DE DATOS ---
try:
    clientes_files = list_excel_files(FOLDER_CLIENTES)
    listas_files = list_excel_files(FOLDER_LISTAS)
    df_clientes = read_excel_from_drive(clientes_files[0]['id']) if clientes_files else pd.DataFrame()
    df_listas = read_excel_from_drive(listas_files[0]['id']) if listas_files else pd.DataFrame()
except Exception as e:
    st.error(f"Error inicial de carga: {e}")

# --- CARGA DE IA LOCAL (CACHÉ PARA QUE NO TARDE CADA VEZ QUE BUSQUES) ---
@st.cache_resource
def load_ai_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

# Pre-calculamos los vectores de los productos para que la búsqueda sea instantánea
@st.cache_data
def get_product_vectors(_df):
    if _df.empty:
        return np.array([]), []
    nombres = _df.iloc[:, 0].astype(str).tolist()
    model = load_ai_model()
    embeddings = model.encode(nombres)
    return embeddings, nombres

if not df_listas.empty:
    product_embeddings, product_names = get_product_vectors(df_listas)

# --- INTERFAZ ---
st.title("🤖 Sistema de Pedidos con IA")
st.divider()

# 1. CLIENTE (Igual que antes)
st.subheader("👤 Seleccionar Cliente")
busqueda_cliente = st.text_input("🔎 Buscar cliente por código o nombre:")
if busqueda_cliente and not df_clientes.empty:
    df_filtro_clientes = df_clientes[df_clientes.astype(str).apply(lambda x: x.str.contains(busqueda_cliente, case=False)).any(axis=1)]
    if not df_filtro_clientes.empty:
        opciones = [f"{str(r.iloc[0])} - {str(r.iloc[1])}" for _, r in df_filtro_clientes.iterrows()]
        sel = st.selectbox("Resultados:", opciones)
        if sel:
            st.session_state.cliente_actual = sel.split(" - ", 1)[1]
            st.success(f"✅ Cliente: **{st.session_state.cliente_actual}**")
    else: st.info("Cliente no encontrado.")
elif st.session_state.cliente_actual:
    st.success(f"✅ Cliente actual: **{st.session_state.cliente_actual}**")

st.divider()

# 2. BUSCADOR INTELIGENTE (IA local)
if st.session_state.cliente_actual and not df_listas.empty:
    st.subheader("📦 Buscar Productos (Búsqueda Inteligente)")
    busqueda_producto = st.text_input("🔎 Describe el producto (escribe 'tarugo', 'martillo', etc.):")

    if busqueda_producto:
        with st.spinner("🤖 La IA está analizando tu búsqueda..."):
            # Convertimos la búsqueda del usuario en un vector
            model = load_ai_model()
            query_vector = model.encode([busqueda_producto])
            
            # Calculamos la similitud contra TODOS los productos
            similarities = cosine_similarity(query_vector, product_embeddings)[0]
            
            # Ordenamos los productos de mayor a menor similitud
            top_indices = similarities.argsort()[-10:][::-1] # Tomamos los 10 mejores
            
            # Mostramos resultados
            st.markdown("**Resultados encontrados por similitud:**")
            encontro_algo = False
            for idx in top_indices:
                if similarities[idx] > 0.3: # Si la similitud es superior al 30% lo mostramos
                    encontro_algo = True
                    nombre = product_names[idx]
                    precio = df_listas.iloc[idx, 1]
                    
                    with st.container(border=True):
                        cols = st.columns([3, 1, 1, 1])
                        with cols[0]: st.markdown(f"**{nombre}**")
                        with cols[1]: st.markdown(f"💰 ${precio:,.2f} c/u")
                        with cols[2]:
                            cant = st.number_input("Cant.", min_value=1, step=1, value=1, key=f"cant_{idx}")
                        with cols[3]:
                            if st.button("➕ Agregar", key=f"btn_{idx}"):
                                st.session_state.pedido.append({
                                    "Producto": nombre, "Cantidad": cant, 
                                    "Precio Unitario": precio, "Total": cant * precio
                                })
                                st.rerun()
            if not encontro_algo:
                st.info("La IA buscó el producto, pero no encontró una coincidencia fuerte (prueba con otras palabras).")

# 3. CARRITO DE PEDIDOS
st.divider()
if st.session_state.pedido:
    df_pedido = pd.DataFrame(st.session_state.pedido)
    df_resumen = df_pedido.groupby("Producto").agg({"Cantidad":"sum", "Precio Unitario":"first", "Total":"sum"}).reset_index()
    st.subheader("🧾 Resumen del Pedido")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    with col2:
        total = df_resumen['Total'].sum()
        st.metric(label="💰 TOTAL DEL PEDIDO", value=f"$ {total:,.2f}")
        if st.button("🧹 Vaciar carrito", type="primary"):
            st.session_state.pedido = []
            st.session_state.cliente_actual = None
            st.rerun()
else:
    st.info("El carrito está vacío. Selecciona un cliente y busca un producto con IA.")
