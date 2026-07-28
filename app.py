import streamlit as st
import pandas as pd
from drive_utils import list_excel_files, read_excel_from_drive

# --- CONFIGURACIÓN DE PÁGINA (Estilo Delivery) ---
st.set_page_config(
    page_title="Sistema de Pedidos",
    page_icon="🍔",
    layout="wide"
)

# --- ESTADO DE LA SESIÓN (Carrito y Cliente) ---
if 'pedido' not in st.session_state:
    st.session_state.pedido = []
if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = None

# --- IDS DE LAS CARPETAS DE DRIVE (Ocultos para el usuario final) ---
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrIPeCaN2xwOAf5Bue" 
FOLDER_LISTAS   = "1COsdgql81C20ePt41qTagXgMZ5RnmnGu"   

# --- CARGA DE DATOS (Detrás de escena) ---
try:
    clientes_files = list_excel_files(FOLDER_CLIENTES)
    listas_files = list_excel_files(FOLDER_LISTAS)
    
    # Cargamos los DataFrames completos en segundo plano
    if clientes_files:
        df_clientes = read_excel_from_drive(clientes_files[0]['id']) # Toma el primer archivo de la carpeta clientes
    else:
        df_clientes = pd.DataFrame()

    if listas_files:
        df_listas = read_excel_from_drive(listas_files[0]['id']) # Toma el primer archivo de la carpeta listas
    else:
        df_listas = pd.DataFrame()

except Exception as e:
    st.error(f"Error inicial al cargar los datos: {e}")

# --- INTERFAZ DE USUARIO ---
st.title("🍔 Sistema de Armado de Pedidos")

# --- 1. BUSCADOR DE CLIENTES ---
st.subheader("👤 1. ¿Para quién es el pedido?")
busqueda_cliente = st.text_input("🔎 Buscar cliente por nombre o código:", placeholder="Escribí el nombre del cliente...")

if busqueda_cliente and not df_clientes.empty:
    # Filtrar clientes
    df_filtro_clientes = df_clientes[df_clientes.astype(str).apply(lambda x: x.str.contains(busqueda_cliente, case=False)).any(axis=1)]
    
    if not df_filtro_clientes.empty:
        # Mostramos los resultados como botones o selección (usaremos botones estilo app)
        cols = st.columns(3)
        for i, (index, row) in enumerate(df_filtro_clientes.iterrows()):
            nombre_cliente = row.iloc[0] # Asume que el nombre está en la 1ra columna
            with cols[i % 3]:
                if st.button(f"📌 {nombre_cliente}", key=f"btn_cli_{i}"):
                    st.session_state.cliente_actual = nombre_cliente
                    st.rerun()
    else:
        st.info("No se encontró ese cliente.")

# Mostrar cliente seleccionado
if st.session_state.cliente_actual:
    st.success(f"✅ Cliente seleccionado: **{st.session_state.cliente_actual}**")
    st.divider()

# --- 2. BUSCADOR DE PRODUCTOS (Solo se muestra si hay cliente seleccionado) ---
if st.session_state.cliente_actual:
    st.subheader("🛒 2. ¿Qué va a llevar?")
    busqueda_producto = st.text_input("🔎 Buscar producto por nombre o código:", placeholder="Escribí el producto...")

    if busqueda_producto and not df_listas.empty:
        # Filtrar productos
        df_filtro_productos = df_listas[df_listas.astype(str).apply(lambda x: x.str.contains(busqueda_producto, case=False)).any(axis=1)]
        
        if not df_filtro_productos.empty:
            st.markdown("**Resultados de la búsqueda:**")
            # Creamos "tarjetas" de productos
            cols = st.columns(2)
            for i, (index, row) in enumerate(df_filtro_productos.iterrows()):
                nombre = row.iloc[0] # Nombre del producto (Col 0)
                precio = row.iloc[1] # Precio (Col 1)
                
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{nombre}**")
                        st.markdown(f"💰 Precio unitario: **${precio:,.2f}**")
                        if st.button(f"➕ Agregar 1 unidad", key=f"btn_prod_{i}"):
                            # Buscar el precio real exacto
                            precio_real = df_listas[df_listas.iloc[:, 0] == nombre].iloc[0, 1]
                            st.session_state.pedido.append({
                                "Producto": nombre,
                                "Cantidad": 1,
                                "Precio Unitario": precio_real,
                                "Total": precio_real
                            })
                            st.rerun()
        else:
            st.info("No se encontraron productos con ese nombre.")
    
    st.divider()

# --- 3. CARRITO DE PEDIDOS (Siempre visible abajo) ---
st.subheader("📦 Resumen del Pedido")

if st.session_state.pedido:
    df_pedido = pd.DataFrame(st.session_state.pedido)
    
    # Agrupamos por producto para que se vea más limpio
    df_resumen = df_pedido.groupby("Producto").agg({
        "Cantidad": "sum",
        "Precio Unitario": "first",
        "Total": "sum"
    }).reset_index()
    
    # Mostramos el carrito
    col1, col2 = st.columns([3, 1])
    with col1:
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    with col2:
        total_pedido = df_resumen['Total'].sum()
        st.markdown("### 💰 Total:")
        st.markdown(f"## $ {total_pedido:,.2f}")
        st.divider()
        if st.button("🧹 Vaciar carrito", type="primary"):
            st.session_state.pedido = []
            st.rerun()
else:
    st.info("El carrito está vacío. Selecciona un cliente y agrega productos.")
