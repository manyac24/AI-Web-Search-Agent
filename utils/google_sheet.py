import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json
import tempfile
import pandas as pd
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# CREDENTIALS_FILE = 'client_Secret.json'

google_oauth_secrets = st.secrets["google_oauth"]

# Convert the credentials into the format needed for OAuth
oauth_data = {
    "web": {
        "client_id": google_oauth_secrets["client_id"],
        "project_id": google_oauth_secrets["project_id"],
        "auth_uri": google_oauth_secrets["auth_uri"],
        "token_uri": google_oauth_secrets["token_uri"],
        "auth_provider_x509_cert_url": google_oauth_secrets["auth_provider_x509_cert_url"],
        "client_secret": google_oauth_secrets["client_secret"],
        "javascript_origins": google_oauth_secrets["javascript_origins"],
        "redirect_uris": json.loads(google_oauth_secrets["redirect_uris"]),
    }
}
with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
    tmp_file.write(json.dumps(oauth_data).encode())
    tmp_file_path = tmp_file.name
    
def create_oauth_flow():
    """Create OAuth2 flow instance to manage the OAuth 2.0 Authorization Grant Flow"""
    flow = Flow.from_client_secrets_file(
        tmp_file_path,
        scopes=SCOPES,
        redirect_uri=google_oauth_secrets["redirect_uris"][1]
    )
    flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
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
