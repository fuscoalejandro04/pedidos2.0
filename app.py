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

# --- IDS DE LAS CARPETAS DE DRIVE (YA ACTUALIZADOS) ---
# Reemplazados con los IDs exactos que me diste
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrIPeCaN2xwOAf5Bue" 
FOLDER_LISTAS   = "1COsdgql81C20ePt41qTagXgMZ5RnmnGu"   

# --- CARGA DE ARCHIVOS (CLIENTES) ---
st.subheader("👤 Base de Datos de Clientes")

try:
    clientes_files = list_excel_files(FOLDER_CLIENTES)

    if not clientes_files:
        st.warning("No se encontraron archivos en la carpeta 'clientes'.")
    else:
        clientes_opciones = {f['name']: f['id'] for f in clientes_files}
        cliente_seleccionado = st.selectbox("Selecciona la base de clientes:", list(clientes_opciones.keys()))

        if cliente_seleccionado:
            cliente_id = clientes_opciones[cliente_seleccionado]
            with st.spinner("Cargando base de clientes..."):
                df_clientes = read_excel_from_drive(cliente_id)
                st.success(f"✅ Base de clientes cargada: {cliente_seleccionado}")
                st.dataframe(df_clientes, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la base de clientes: {e}")

st.divider()

# --- CARGA DE ARCHIVOS (LISTAS DE PRECIOS) ---
st.subheader("💰 Lista de Precios")

try:
    listas_files = list_excel_files(FOLDER_LISTAS)

    if not listas_files:
        st.warning("No se encontraron archivos en la carpeta 'listas'.")
    else:
        listas_opciones = {f['name']: f['id'] for f in listas_files}
        lista_seleccionada = st.selectbox("Selecciona la lista de precios:", list(listas_opciones.keys()))

        if lista_seleccionada:
            lista_id = listas_opciones[lista_seleccionada]
            with st.spinner("Cargando lista de precios..."):
                df_listas = read_excel_from_drive(lista_id)
                st.success(f"✅ Lista de precios cargada: {lista_seleccionada}")
                st.dataframe(df_listas, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la lista de precios: {e}")
