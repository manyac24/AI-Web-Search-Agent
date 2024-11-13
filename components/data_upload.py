import streamlit as st
from utils.google_sheet import *
from components.prompt_template import render_prompt_template_section




def render_upload_tabs():
     # Create tabs for different upload methods
    tab1, tab2 = st.tabs(["CSV Upload", "Google Sheets"])
    
    # CSV Upload Tab
    with tab1:
        st.header("Upload CSV File")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                st.session_state.df = pd.read_csv(uploaded_file)
                st.success("File successfully uploaded!")
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
    
    # Google Sheets Tab
    with tab2:
        st.header("Connect to Google Sheets")
        if  st.query_params:
            flow = create_oauth_flow()
            try:
                flow.fetch_token(code=st.query_params.code)
                st.session_state['credentials'] = flow.credentials
                st.success("Successfully authenticated!")
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
            

         # If the user hasn't been redirected, show the sign-in button
        if st.session_state.get('credentials') is None:
            if st.button("Sign in with Google"):
                flow = create_oauth_flow()
                authorization_url, state = flow.authorization_url()
                st.markdown(f'Click [here]({authorization_url}) to authorize access')
                st.session_state['oauth_state'] = state
                
                auth_code = st.text_input("Enter the authorization code:")
                if auth_code:
                    #try:
                        flow.fetch_token(code=auth_code)
                        st.session_state.credentials = flow.credentials
                        st.success("Successfully authenticated!")
                        st.rerun()
                    # except Exception as e:
                    #     st.error(f"Authentication failed: {str(e)}")
        
        else:
            st.success("✓ Connected to Google Account")
            
            sheet_url = st.text_input(
                "Enter Google Sheet URL",
                value=st.session_state.sheet_url,
                help="Paste the full URL of your Google Sheet"
            )
            
            if sheet_url:
                spreadsheet_id = parse_sheet_url(sheet_url)
                if spreadsheet_id:
                    try:
                        service = get_google_sheets_service(st.session_state.credentials)
                        st.session_state.df = load_sheet_data(service, spreadsheet_id)
                        st.session_state.sheet_url = sheet_url
                    except Exception as e:
                        st.error(f"Error loading sheet: {str(e)}")


       # Display data preview and column selection if data is loaded
    if st.session_state.df is not None:
        st.header("Data Preview and Column Selection")
        
        # Display available columns
        st.subheader("Available Columns")
        columns = st.session_state.df.columns.tolist()
        selected_column = st.selectbox(
            "Select the main column (e.g., company names)",
            options=columns
        )
        
        # Display data preview
        st.subheader("Data Preview")
        st.dataframe(st.session_state.df.head(5))
        
        # Display basic statistics
        st.subheader("Data Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", len(st.session_state.df))
        with col2:
            st.metric("Total Columns", len(st.session_state.df.columns))
        with col3:
            st.metric("Selected Column Unique Values", 
                     st.session_state.df[selected_column].nunique() if selected_column else 0)
        
        # Add the prompt template section
        if selected_column:
            st.markdown("---")
            render_prompt_template_section(st.session_state.df, selected_column)        

    # Add search execution section
    # if st.session_state.df is not None and selected_column:   
    #     render_search_execution(selected_column)