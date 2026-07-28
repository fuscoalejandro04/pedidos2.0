import streamlit as st
import pandas as pd
from drive_utils import list_excel_files, read_excel_from_drive

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Carga de Pedidos",
    page_icon="📦",
    layout="centered"
)

st.title("📦 Carga de Pedidos desde Lista de Precios")
st.divider()

# --- INICIALIZAR EL CARRITO DE COMPRAS EN LA MEMORIA ---
if 'pedido' not in st.session_state:
    st.session_state.pedido = []

# --- IDS DE LAS CARPETAS DE DRIVE ---
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrIPeCaN2xwOAf5Bue" 
FOLDER_LISTAS   = "1COsdgql81C20ePt41qTagXgMZ5RnmnGu"   

# --- CARGA DE CLIENTES ---
st.subheader("👤 Base de Datos de Clientes")
try:
    clientes_files = list_excel_files(FOLDER_CLIENTES)
    if clientes_files:
        clientes_opciones = {f['name']: f['id'] for f in clientes_files}
        cliente_seleccionado = st.selectbox("Selecciona la base de clientes:", list(clientes_opciones.keys()))
        if cliente_seleccionado:
            with st.spinner("Cargando base de clientes..."):
                df_clientes = read_excel_from_drive(clientes_opciones[cliente_seleccionado])
                st.success(f"✅ Base de clientes cargada: {cliente_seleccionado}")
                st.dataframe(df_clientes, use_container_width=True)
except Exception as e:
    st.error(f"Error al cargar clientes: {e}")

st.divider()

# --- CARGA DE LISTA DE PRECIOS + BUSCADOR + CARRITO ---
st.subheader("💰 Lista de Precios y Armado de Pedido")
try:
    listas_files = list_excel_files(FOLDER_LISTAS)
    if listas_files:
        listas_opciones = {f['name']: f['id'] for f in listas_files}
        lista_seleccionada = st.selectbox("Selecciona la lista de precios:", list(listas_opciones.keys()))
        
        if lista_seleccionada:
            with st.spinner("Cargando lista de precios..."):
                df_listas = read_excel_from_drive(listas_opciones[lista_seleccionada])
                
                # --- BUSCADOR DE PRODUCTOS ---
                st.markdown("### 🔍 Buscador de productos")
                busqueda = st.text_input("Escribe el nombre del producto o código:")
                
                if busqueda:
                    # Filtra el dataframe mostrando solo las filas que coincidan con la búsqueda
                    df_filtrado = df_listas[df_listas.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
                else:
                    df_filtrado = df_listas

                # --- AGREGAR AL CARRITO ---
                st.markdown("### 🛒 Agregar al pedido")
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    opciones_productos = df_filtrado.iloc[:, 0].tolist() # Asume que la columna 0 es el nombre del producto
                    producto_seleccionado = st.selectbox("Selecciona un producto:", opciones_productos)
                with col2:
                    cantidad = st.number_input("Cantidad:", min_value=1, step=1, value=1)
                
                if st.button("➕ Agregar al pedido"):
                    if producto_seleccionado:
                        # Buscar el precio real en el dataframe
                        precio_unitario = df_listas[df_listas.iloc[:, 0] == producto_seleccionado].iloc[0, 1] # Asume columna 1 es precio
                        st.session_state.pedido.append({
                            "Producto": producto_seleccionado,
                            "Cantidad": cantidad,
                            "Precio Unitario": precio_unitario,
                            "Total": cantidad * precio_unitario
                        })
                        st.success(f"Agregado {cantidad} unidad(es) de {producto_seleccionado} al pedido.")
                        st.rerun() # Recarga la página para actualizar el carrito

                # --- VER EL CARRITO ---
                if st.session_state.pedido:
                    st.markdown("### 📦 Tu Pedido Actual")
                    df_pedido = pd.DataFrame(st.session_state.pedido)
                    st.dataframe(df_pedido, use_container_width=True)
                    
                    total_pedido = df_pedido['Total'].sum()
                    st.success(f"💰 **Total del pedido: ${total_pedido:,.2f}**")
                    
                    if st.button("🧹 Vaciar carrito"):
                        st.session_state.pedido = []
                        st.rerun()
                else:
                    st.info("El carrito está vacío. Busca y agrega productos arriba.")
                    
except Exception as e:
    st.error(f"Error al cargar lista de precios: {e}")
