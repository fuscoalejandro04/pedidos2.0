import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    # Usa las credenciales que guardaste en los Secretos de Streamlit
    creds = Credentials.from_service_account_info(st.secrets, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def list_excel_files():
    service = get_drive_service()
    # Busca archivos de Excel en tu Drive
    results = service.files().list(
        q="mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel'",
        pageSize=50, fields="nextPageToken, files(id, name)").execute()
    return results.get('files', [])

def read_excel_from_drive(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    file_data = request.execute()
    # Convierte el archivo descargado en un DataFrame de pandas
    df = pd.read_excel(io.BytesIO(file_data))
    return df
