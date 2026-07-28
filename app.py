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

# --- ID DE LA CARPETA DE DRIVE ---
# Reemplaza con el ID de la carpeta "clientes" que capturaste:
FOLDER_CLIENTES = "1NeBhwrAWxPdrScjrPeCaN2xwOAf5Bue" 

# --- LÓGICA DE LA APP ---
st.subheader("👤 Seleccionar Cliente")

try:
    # Obtener la lista de archivos Excel de la carpeta
    clientes_files = list_excel_files(FOLDER_CLIENTES)

    if not clientes_files:
        st.warning("No se encontraron archivos Excel en la carpeta de Drive especificada.")
    else:
        # Crear una lista con los nombres de los archivos
        file_options = {file['name']: file['id'] for file in clientes_files}
        selected_file_name = st.selectbox("Selecciona un archivo de precios:", list(file_options.keys()))

        if selected_file_name:
            file_id = file_options[selected_file_name]
            
            with st.spinner("Cargando archivo desde Google Drive..."):
                # Leer el Excel seleccionado
                df = read_excel_from_drive(file_id)
                
                st.success(f"✅ Archivo cargado exitosamente: {selected_file_name}")
                st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Ocurrió un error al conectar con Drive: {e}")
