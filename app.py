import streamlit as st
import pandas as pd
from drive_utils import list_excel_files, read_excel_from_drive

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema de Pedidos", page_icon="🛠️", layout="wide")

# --- ESTADO DE SESIÓN ---
if 'pedido' not in st.session_state:
    st.session_state.pedido = []
if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = None

# --- IDS DE DRIVE ---
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrIPeCaN2xwOAf5Bue" 
FOLDER_LISTAS   = "1COsdgql81C20ePt41qTagXgMZ5RnmnGu"   

# --- CARGA DE DATOS OCULTA ---
try:
    clientes_files = list_excel_files(FOLDER_CLIENTES)
    listas_files = list_excel_files(FOLDER_LISTAS)
    df_clientes = read_excel_from_drive(clientes_files[0]['id']) if clientes_files else pd.DataFrame()
    df_listas = read_excel_from_drive(listas_files[0]['id']) if listas_files else pd.DataFrame()
except Exception as e:
    st.error(f"Error inicial de carga: {e}")

# --- TÍTULO ---
st.title("🛠️ Sistema de Pedidos")
st.divider()

# --- 1. BUSCADOR DE CLIENTES ---
st.subheader("👤 1. Seleccionar Cliente")
busqueda_cliente = st.text_input("🔎 Buscar cliente por código o nombre:", placeholder="Ej: 1221 o López")

if busqueda_cliente and not df_clientes.empty:
    df_filtro_clientes = df_clientes[df_clientes.astype(str).apply(lambda x: x.str.contains(busqueda_cliente, case=False)).any(axis=1)]
    
    if not df_filtro_clientes.empty:
        opciones_formato = []
        for _, row in df_filtro_clientes.iterrows():
            opciones_formato.append(f"{str(row.iloc[0])} - {str(row.iloc[1])}")
        cliente_seleccionado_txt = st.selectbox("Resultados encontrados:", opciones_formato)
        if cliente_seleccionado_txt:
            st.session_state.cliente_actual = cliente_seleccionado_txt.split(" - ", 1)[1]
            st.success(f"✅ Cliente seleccionado: **{st.session_state.cliente_actual}**")
    else:
        st.info("No se encontró ningún cliente con ese término.")
elif not busqueda_cliente and st.session_state.cliente_actual:
    st.success(f"✅ Cliente actual: **{st.session_state.cliente_actual}**")

st.divider()

# --- 2. BUSCADOR DE PRODUCTOS ---
if st.session_state.cliente_actual:
    st.subheader("📦 2. Agregar Productos")
    busqueda_producto = st.text_input("🔎 Buscar producto por código o nombre:", placeholder="Ej: Martillo, Taladro")
    
    if busqueda_producto and not df_listas.empty:
        df_filtro_productos = df_listas[df_listas.astype(str).apply(lambda x: x.str.contains(busqueda_producto, case=False)).any(axis=1)]
        
        if not df_filtro_productos.empty:
            st.markdown("**Resultados:**")
            for i, (index, row) in enumerate(df_filtro_productos.iterrows()):
                nombre = row.iloc[0]
                precio = row.iloc[1]
                with st.container(border=True):
                    cols = st.columns([3, 1, 1, 1])
                    with cols[0]: st.markdown(f"**{nombre}**")
                    with cols[1]: st.markdown(f"💰 ${precio:,.2f} c/u")
                    with cols[2]:
                        cantidad = st.number_input("Cant.", min_value=1, step=1, value=1, key=f"cant_{i}")
                    with cols[3]:
                        if st.button("➕ Agregar", key=f"btn_{i}"):
                            st.session_state.pedido.append({
                                "Producto": nombre, "Cantidad": cantidad, 
                                "Precio Unitario": precio, "Total": cantidad * precio
                            })
                            st.rerun()
        else:
            st.info("No se encontraron productos con ese nombre.")
    
    st.divider()

# --- 3. CARRITO Y TOTAL ---
st.subheader("🧾 Resumen del Pedido")
if st.session_state.pedido:
    df_pedido = pd.DataFrame(st.session_state.pedido)
    df_resumen = df_pedido.groupby("Producto").agg({"Cantidad":"sum", "Precio Unitario":"first", "Total":"sum"}).reset_index()
    
    col1, col2 = st.columns([3, 1])
    with col1: st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    with col2:
        total = df_resumen['Total'].sum()
        st.metric(label="💰 TOTAL DEL PEDIDO", value=f"$ {total:,.2f}")
        st.divider()
        if st.button("🧹 Vaciar carrito y empezar de nuevo", type="primary"):
            st.session_state.pedido = []
            st.session_state.cliente_actual = None
            st.rerun()
else:
    st.info("El carrito está vacío. Selecciona un cliente y agrega productos.")
