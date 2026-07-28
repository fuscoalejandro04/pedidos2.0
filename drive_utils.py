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
    
    # Consulta base: buscar archivos Excel
    query = "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel'"
    
    # Si el usuario pasó un ID de carpeta, buscar solo dentro de esa carpeta
    if folder_id:
        query = f"parents='{folder_id}' and ({query})"
        
    results = service.files().list(q=query, pageSize=50, fields="nextPageToken, files(id, name)").execute()
    return results.get('files', [])

def read_excel_from_drive(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    file_data = request.execute()
    df = pd.read_excel(io.BytesIO(file_data))
    return df
