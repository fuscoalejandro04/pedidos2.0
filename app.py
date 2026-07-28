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

# --- BUSCADOR DE PRODUCTOS (SIN MOSTRAR LA LISTA COMPLETA) ---
st.subheader("🔍 Buscador de Productos y Precios")

try:
    listas_files = list_excel_files(FOLDER_LISTAS)
    if listas_files:
        listas_opciones = {f['name']: f['id'] for f in listas_files}
        lista_seleccionada = st.selectbox("Selecciona la lista de precios a consultar:", list(listas_opciones.keys()))
        
        if lista_seleccionada:
            with st.spinner("Cargando base de datos de precios..."):
                # Cargamos el dataframe, pero NO lo mostramos en pantalla
                df_listas = read_excel_from_drive(listas_opciones[lista_seleccionada])
                
                # --- SOLO EL BUSCADOR ---
                busqueda = st.text_input("🔎 Escribe el nombre o código del producto que buscas:")
                
                # Si el usuario escribió algo, filtramos los resultados
                if busqueda:
                    # Filtra buscando en cualquier columna del dataframe
                    df_filtrado = df_listas[df_listas.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
                    
                    if df_filtrado.empty:
                        st.warning("⚠️ No se encontraron productos con ese término de búsqueda.")
                    else:
                        st.success(f"Se encontraron {len(df_filtrado)} producto(s):")
                        
                        # --- MOSTRAMOS LOS PRODUCTOS FILTRADOS CON DETALLES ---
                        # Asumimos que la Columna 0 es el Nombre y la Columna 1 es el Precio
                        # (Si tu Excel tiene otros nombres de columna, puedes ajustarlo aquí)
                        st.markdown("**Resultados de la búsqueda:**")
                        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
                        
                        st.markdown("---")
                        st.markdown("### 🛒 Agregar al pedido")
                        
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            # Dropdown con los nombres de los productos filtrados
                            producto_seleccionado = st.selectbox("Elige un producto de los resultados:", df_filtrado.iloc[:, 0].tolist())
                        
                        with col2:
                            cantidad = st.number_input("Cantidad:", min_value=1, step=1, value=1)
                        
                        # Botón para agregar al carrito
                        if st.button("➕ Agregar al pedido"):
                            if producto_seleccionado:
                                # Obtener el precio exacto del producto seleccionado en el DataFrame
                                precio_unitario = df_listas[df_listas.iloc[:, 0] == producto_seleccionado].iloc[0, 1]
                                
                                # Guardar en el carrito de la sesión
                                st.session_state.pedido.append({
                                    "Producto": producto_seleccionado,
                                    "Cantidad": cantidad,
                                    "Precio Unitario": precio_unitario,
                                    "Total": cantidad * precio_unitario
                                })
                                st.success(f"✅ Agregado: {cantidad} x {producto_seleccionado}")
                                st.rerun() # Recarga para actualizar la visualización del carrito
                else:
                    # Si no hay búsqueda, mostramos un mensaje sutil
                    st.info("💡 Escribe arriba para buscar y agregar productos al pedido.")

                # --- VISUALIZADOR DEL CARRITO (SIEMPRE VISIBLE ABAJO) ---
                st.divider()
                if st.session_state.pedido:
                    st.subheader("📦 Tu Pedido Actual")
                    df_pedido = pd.DataFrame(st.session_state.pedido)
                    st.dataframe(df_pedido, use_container_width=True, hide_index=True)
                    
                    total_pedido = df_pedido['Total'].sum()
                    st.success(f"💰 **Total del pedido: ${total_pedido:,.2f}**")
                    
                    if st.button("🧹 Vaciar carrito"):
                        st.session_state.pedido = []
                        st.rerun()
                else:
                    st.info("El carrito de pedidos está vacío.")
                    
except Exception as e:
    st.error(f"Error al cargar la lista de precios: {e}")
