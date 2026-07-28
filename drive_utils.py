import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = Credentials.from_service_account_info(st.secrets, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def list_excel_files(folder_id=None):
    service = get_drive_service()
    
    # --- CONSULTA ACTUALIZADA ---
    # Busca hojas de Google, archivos .xlsx y .xls
    query = "mimeType='application/vnd.google-apps.spreadsheet' or mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel'"
    
    # Filtro por carpeta
    if folder_id:
        query = f"parents='{folder_id}' and ({query})"
        
    results = service.files().list(q=query, pageSize=50, fields="nextPageToken, files(id, name)").execute()
    return results.get('files', [])

def read_excel_from_drive(file_id):
    service = get_drive_service()
    try:
        # 1. Obtener el tipo de archivo para saber si es una Hoja de Google
        file_metadata = service.files().get(fileId=file_id, fields="mimeType").execute()
        mime_type = file_metadata.get('mimeType')
        
        # 2. Descargar el archivo (si es Hoja de Google, convertirla a Excel en el vuelo)
        if mime_type == 'application/vnd.google-apps.spreadsheet':
            request = service.files().export_media(
                fileId=file_id, 
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            request = service.files().get_media(fileId=file_id)
            
        file_data = request.execute()
        df = pd.read_excel(io.BytesIO(file_data))
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo de Drive: {e}")
        return pd.DataFrame()
