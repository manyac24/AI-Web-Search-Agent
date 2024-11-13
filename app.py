import streamlit as st
import os
from components.data_upload import render_upload_tabs


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


def initialize_session_state():
    """Initialize session state variables"""
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None
    if 'sheet_url' not in st.session_state:
        st.session_state.sheet_url = ""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'prompt_template' not in st.session_state:
        st.session_state.prompt_template = ""
    if 'preview_queries' not in st.session_state:
        st.session_state.preview_queries = []

def main():
    st.title("Data Upload Dashboard")
    
    initialize_session_state()
    
    render_upload_tabs()     
       
if __name__ == "__main__":
            main()