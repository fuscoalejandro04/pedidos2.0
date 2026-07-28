import streamlit as st
import pandas as pd
from drive_utils import list_excel_files, read_excel_from_drive

# IDs de las carpetas en Drive (cámbialos por los tuyos)
FOLDER_PRECIOS = "ID_DE_LA_CARPETA_LISTAS"
FOLDER_CLIENTES = "ID_DE_LA_CARPETA_CLIENTES"

st.set_page_config(page_title="Gestor de Pedidos", layout="wide")
st.title("📦 Carga de Pedidos desde Lista de Precios")

# 1. Seleccionar cliente
st.subheader("👤 Seleccionar Cliente")
clientes_files = list_excel_files(FOLDER_CLIENTES)
if not clientes_files:
    st.warning("No se encontraron archivos de clientes en la carpeta.")
else:
    cliente_nombres = {f['name']: f['id'] for f in clientes_files}
    cliente_seleccionado = st.selectbox("Archivo de clientes", list(cliente_nombres.keys()))
    if cliente_seleccionado:
        df_clientes = read_excel_from_drive(cliente_nombres[cliente_seleccionado])
        # Suponiendo que el Excel tiene una columna "Cliente" o "Nombre"
        # Ajusta el nombre de la columna según tu archivo
        lista_clientes = df_clientes['Cliente'].tolist()  # o 'Nombre'
        cliente = st.selectbox("Cliente", lista_clientes)
        st.success(f"Cliente seleccionado: {cliente}")

# 2. Seleccionar lista de precios
st.subheader("📋 Lista de Precios")
precios_files = list_excel_files(FOLDER_PRECIOS)
if not precios_files:
    st.warning("No se encontraron archivos de lista de precios.")
else:
    precios_nombres = {f['name']: f['id'] for f in precios_files}
    seleccion = st.selectbox("Selecciona la lista de precios", list(precios_nombres.keys()))
    if seleccion:
        file_id = precios_nombres[seleccion]
        df = read_excel_from_drive(file_id)
        st.dataframe(df)

        # 3. Armar pedido
        st.subheader("🛒 Armar Pedido")
        # Suponemos columnas: 'Artículo' y 'Precio'
        articulos = df['Artículo'].tolist()
        precios = dict(zip(df['Artículo'], df['Precio']))

        if 'pedido' not in st.session_state:
            st.session_state.pedido = []

        with st.form("agregar_item"):
            producto = st.selectbox("Artículo", articulos)
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            agregar = st.form_submit_button("Agregar al pedido")
            if agregar:
                st.session_state.pedido.append({
                    'Cliente': cliente if 'cliente' in locals() else 'No definido',
                    'Artículo': producto,
                    'Cantidad': cantidad,
                    'Precio unitario': precios[producto],
                    'Subtotal': cantidad * precios[producto]
                })
                st.success(f"Agregado {producto} x {cantidad}")

        # Mostrar resumen
        if st.session_state.pedido:
            df_pedido = pd.DataFrame(st.session_state.pedido)
            st.subheader("📄 Pedido actual")
            st.dataframe(df_pedido)
            st.write(f"**Total:** ${df_pedido['Subtotal'].sum():.2f}")

            if st.button("Guardar pedido"):
                # Guardar en CSV o en Drive (opcional)
                df_pedido.to_csv("pedido_guardado.csv", index=False)
                st.success("Pedido guardado localmente")
