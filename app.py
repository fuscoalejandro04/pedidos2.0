import streamlit as st
import pandas as pd
from drive_utils import list_excel_files, read_excel_from_drive

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Pedidos Mayorista",
    page_icon="🛠️",
    layout="wide"
)

# --- ESTADO DE LA SESIÓN ---
if 'pedido' not in st.session_state:
    st.session_state.pedido = []
if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = None

# --- IDS DE LAS CARPETAS ---
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrIPeCaN2xwOAf5Bue" 
FOLDER_LISTAS   = "1COsdgql81C20ePt41qTagXgMZ5RnmnGu"   

# --- CARGA DE DATOS EN SEGUNDO PLANO ---
try:
    clientes_files = list_excel_files(FOLDER_CLIENTES)
    listas_files = list_excel_files(FOLDER_LISTAS)
    
    df_clientes = read_excel_from_drive(clientes_files[0]['id']) if clientes_files else pd.DataFrame()
    df_listas = read_excel_from_drive(listas_files[0]['id']) if listas_files else pd.DataFrame()

except Exception as e:
    st.error(f"Error de conexión inicial: {e}")

# --- 1. SELECCIÓN DE CLIENTE (MÁS INTUITIVO) ---
st.title("🛠️ Sistema de Pedidos")
st.divider()

st.subheader("👤 1. Seleccionar Cliente")
busqueda_cliente = st.text_input("🔎 Buscar cliente por código o nombre:", placeholder="Ej: 1221 o López")

if busqueda_cliente and not df_clientes.empty:
    # Buscar en cualquier columna
    df_filtro_clientes = df_clientes[df_clientes.astype(str).apply(lambda x: x.str.contains(busqueda_cliente, case=False)).any(axis=1)]
    
    if not df_filtro_clientes.empty:
        # Creamos las opciones con formato: "[ID] - [Nombre]" 
        # (Asumimos col 0 = ID, col 1 = Nombre. Si en tu Excel es al revés, funciona igual buscando en ambas columnas)
        opciones_formato = []
        for _, row in df_filtro_clientes.iterrows():
            opciones_formato.append(f"{str(row.iloc[0])} - {str(row.iloc[1])}")
        
        # Selectbox nativo de Streamlit (filtra las opciones mientras escribes)
        cliente_seleccionado_txt = st.selectbox("Resultados encontrados:", opciones_formato)
        
        if cliente_seleccionado_txt:
            # Extraemos el nombre real para guardarlo
            nombre_cliente = cliente_seleccionado_txt.split(" - ", 1)[1]
            st.session_state.cliente_actual = nombre_cliente
            st.success(f"✅ Cliente seleccionado: **{nombre_cliente}**")
    else:
        st.info("No se encontró ningún cliente con ese término.")

elif not busqueda_cliente and st.session_state.cliente_actual:
    st.success(f"✅ Cliente actual: **{st.session_state.cliente_actual}**")

st.divider()

# --- 2. BÚSQUEDA DE PRODUCTOS (Venta Mayorista) ---
if st.session_state.cliente_actual:
    st.subheader("📦 2. Agregar Productos")
    busqueda_producto = st.text_input("🔎 Buscar producto por código o nombre:", placeholder="Ej: Martillo, Taladro, etc.")
    
    if busqueda_producto and not df_listas.empty:
        df_filtro_productos = df_listas[df_listas.astype(str).apply(lambda x: x.str.contains(busqueda_producto, case=False)).any(axis=1)]
        
        if not df_filtro_productos.empty:
            st.markdown("**Resultados de la búsqueda:**")
            
            # Mostramos los productos en formato de fila con campo de cantidad
            for i, (index, row) in enumerate(df_filtro_productos.iterrows()):
                nombre = row.iloc[0] # Nombre del producto (col 0)
                precio = row.iloc[1] # Precio (col 1)
                
                with st.container(border=True):
                    cols = st.columns([3, 1, 1, 1])
                    with cols[0]:
                        st.markdown(f"**{nombre}**")
                    with cols[1]:
                        st.markdown(f"💰 ${precio:,.2f} c/u")
                    with cols[2]:
                        # Campo de cantidad (ideal para mayoristas que necesitan cajas o docenas)
                        cantidad = st.number_input("Cant.", min_value=1, step=1, value=1, key=f"cant_{i}")
                    with cols[3]:
                        if st.button("➕ Agregar al pedido", key=f"btn_{i}"):
                            precio_real = df_listas[df_listas.iloc[:, 0] == nombre].iloc[0, 1]
                            st.session_state.pedido.append({
                                "Producto": nombre,
                                "Cantidad": cantidad,
                                "Precio Unitario": precio_real,
                                "Total": cantidad * precio_real
                            })
                            st.rerun() # Recarga para ver el carrito actualizado
        else:
            st.info("No se encontraron productos con ese nombre.")
    
    st.divider()

# --- 3. CARRITO DE PEDIDOS ---
st.subheader("🧾 Resumen y Factura")

if st.session_state.pedido:
    df_pedido = pd.DataFrame(st.session_state.pedido)
    
    # Agrupamos para mostrar cantidades sumadas
    df_resumen = df_pedido.groupby("Producto").agg({
        "Cantidad": "sum",
        "Precio Unitario": "first",
        "Total": "sum"
    }).reset_index()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    with col2:
        total_pedido = df_resumen['Total'].sum()
        st.metric(label="💰 TOTAL DEL PEDIDO", value=f"$ {total_pedido:,.2f}")
        st.divider()
        if st.button("🧹 Vaciar carrito y empezar de nuevo", type="primary"):
            st.session_state.pedido = []
            st.session_state.cliente_actual = None
            st.rerun()
else:
    st.info("El carrito está vacío. Selecciona un cliente y luego agrega productos.")
