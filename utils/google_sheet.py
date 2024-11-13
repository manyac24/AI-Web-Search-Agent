import streamlit as st
import google_auth_oauthlib
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import pandas as pd
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'client_Secret.json'

def create_oauth_flow():
    """Create OAuth2 flow instance to manage the OAuth 2.0 Authorization Grant Flow"""
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost:8501'
    )
    return flow

def get_google_sheets_service(credentials):
    """Create Google Sheets API service instance"""
    return build('sheets', 'v4', credentials=credentials)

def parse_sheet_url(url):
    """Extract spreadsheet ID from Google Sheets URL"""
    try:
        if '/d/' in url:
            return url.split('/d/')[1].split('/')[0]
        return url
    except:
        return None

def load_sheet_data(service, spreadsheet_id):
    """Load data from Google Sheet"""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range='A1:Z1000'
        ).execute()
        
        values = result.get('values', [])
        if not values:
            st.error('No data found in the Google Sheet')
            return None
            
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
        
    except Exception as e:
        st.error(f"Error accessing Google Sheet: {str(e)}")
        return None
