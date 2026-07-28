import streamlit as st
import pandas as pd
import google.generativeai as genai
from drive_utils import list_excel_files, read_excel_from_drive

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Asistente de Pedidos IA", page_icon="🤖", layout="wide")

# --- INICIALIZACIÓN DE ESTADOS ---
if 'pedido' not in st.session_state:
    st.session_state.pedido = []
if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- CONFIGURACIÓN DE DRIVE ---
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrIPeCaN2xwOAf5Bue" 
FOLDER_LISTAS   = "1COsdgql81C20ePt41qTagXgMZ5RnmnGu"   

# --- CARGA DE DATOS Y CONFIGURACIÓN DE IA ---
try:
    clientes_files = list_excel_files(FOLDER_CLIENTES)
    listas_files = list_excel_files(FOLDER_LISTAS)
    df_clientes = read_excel_from_drive(clientes_files[0]['id']) if clientes_files else pd.DataFrame()
    df_listas = read_excel_from_drive(listas_files[0]['id']) if listas_files else pd.DataFrame()
    
    # Configuramos la IA de Google Gemini con la API Key de los Secretos
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash') # Modelo ultrarrápido y gratuito

    # Creamos un "contexto" para que la IA sepa cuáles son tus productos
    inventario_texto = ""
    if not df_listas.empty:
        inventario_texto = "\n".join([f"- Producto: {row.iloc[0]}, Precio: ${row.iloc[1]}" for _, row in df_listas.iterrows()])
        
except Exception as e:
    st.error(f"Error al cargar datos: {e}")

st.title("🤖 Asistente de Pedidos")

# --- SELECCIÓN DE CLIENTE ---
if not st.session_state.cliente_actual:
    st.subheader("👤 1. Seleccionar Cliente")
    busqueda_cliente = st.text_input("🔎 Buscar cliente por nombre:")
    if busqueda_cliente and not df_clientes.empty:
        df_filtrado = df_clientes[df_clientes.astype(str).apply(lambda x: x.str.contains(busqueda_cliente, case=False)).any(axis=1)]
        if not df_filtrado.empty:
            opciones = [f"{r.iloc[0]} - {r.iloc[1]}" for _, r in df_filtrado.iterrows()]
            sel = st.selectbox("Resultados:", opciones)
            if sel:
                st.session_state.cliente_actual = sel.split(" - ", 1)[1]
                st.success(f"Cliente seleccionado: **{st.session_state.cliente_actual}**")
                st.rerun()
else:
    st.subheader("👤 Cliente actual")
    st.success(f"**{st.session_state.cliente_actual}**")
    if st.button("🔄 Cambiar cliente"):
        st.session_state.cliente_actual = None
        st.rerun()

# --- CHATBOT DE PEDIDOS (SOLO SI HAY CLIENTE SELECCIONADO) ---
if st.session_state.cliente_actual and inventario_texto:
    st.divider()
    st.subheader("💬 Chat de Pedidos")

    # Mostrar el historial del chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input de chat
    if prompt := st.chat_input("Escribe lo que necesitas (ej: 'Busco 5 martillos o algo para madera')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Llamada a la IA
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                system_prompt = f"""Eres un asistente de ventas mayoristas. 
                El cliente actual es {st.session_state.cliente_actual}.
                El inventario disponible es:
                {inventario_texto}
                
                Tu trabajo es ayudar a encontrar productos y sugerir precios. Si el usuario pide algo, pregúntale cuántas unidades quiere y confirma el precio.
                Menciona siempre que el precio es unitario.
                """
                full_prompt = f"{system_prompt}\n\nUsuario: {prompt}"
                response = model.generate_content(full_prompt)
                respuesta_ia = response.text
                
                st.markdown(respuesta_ia)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                
                # --- DETECCIÓN AUTOMÁTICA DE INTENCIÓN DE COMPRA ---
                # Si la IA menciona un producto, le ponemos un botón para agregarlo
                for _, row in df_listas.iterrows():
                    nombre_producto = str(row.iloc[0])
                    if nombre_producto.lower() in respuesta_ia.lower():
                        col_btn, col_price = st.columns([2, 1])
                        with col_btn:
                            if st.button(f"➕ Agregar al carrito: {nombre_producto}", key=f"btn_{nombre_producto}"):
                                st.session_state.pedido.append({
                                    "Producto": nombre_producto, "Cantidad": 1, 
                                    "Precio Unitario": row.iloc[1], "Total": row.iloc[1]
                                })
                                st.rerun()
                        with col_price:
                            st.write(f"Precio: ${row.iloc[1]}")

# --- CARRITO DE PEDIDOS ---
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
        if st.button("🧹 Vaciar carrito y empezar de nuevo", type="primary"):
            st.session_state.pedido = []
            st.rerun()
else:
    st.info("El carrito está vacío. Selecciona un cliente y habla con el chatbot para agregar productos.")
