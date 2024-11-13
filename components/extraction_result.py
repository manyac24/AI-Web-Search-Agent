from typing import List, Dict
import streamlit as st
import pandas as pd
from utils.google_sheet import get_google_sheets_service, parse_sheet_url

def render_extraction_results(results: List[Dict]):
    """Render the extraction results in the dashboard"""
    st.header("Extraction Results")
    
    # Create tabs for different views
    results_tab, analysis_tab, export_tab = st.tabs(["Results", "Analysis", "Export"])
    
    with results_tab:
        # Create a table to display the extracted information
        extract_data = []
        for result in results:
        # for idx, result in enumerate(results):
            extraction_result = result['extraction_result']
            extract_data.append({
                # 'Original_Order': idx, 
                'Entity': result['entity'],
                'Extracted Information': extraction_result['extracted_info'],
                'Confidence': extraction_result['confidence'],
                'Sources': ', '.join(extraction_result['source_urls']),
                'Notes': extraction_result['additional_notes']
            })
        
        extract_df = pd.DataFrame(extract_data)
        # extract_df = extract_df.sort_values('Original_Order').drop('Original_Order', axis=1)
        st.dataframe(extract_df, use_container_width=True)
    
    with analysis_tab:
        # Calculate statistics
        total_processed = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        high_confidence = sum(1 for r in results 
                            if r['extraction_result']['confidence'] == 'HIGH')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Processed", total_processed)
        with col2:
            st.metric("Successful Extractions", successful)
        with col3:
            st.metric("High Confidence Results", high_confidence)
    
    with export_tab:
        # Prepare export data
        export_data = extract_data
        df_export = pd.DataFrame(export_data)
        
        # Offer different export formats
        col1, col2 = st.columns(2)
        with col1:
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="extraction_results.csv",
                mime="text/csv"
            )
        
        with col2:
            
            if st.session_state.credentials:
              if st.button("Extract result to google sheet"):
                # Update Google Sheet
                service = get_google_sheets_service(st.session_state.credentials)
                spreadsheet_id = parse_sheet_url(st.session_state.sheet_url)
                if spreadsheet_id:
                    try:
                            # Get current sheets in the spreadsheet
                            spreadsheet = service.spreadsheets().get(
                                spreadsheetId=spreadsheet_id
                            ).execute()
                            
                            existing_sheets = [sheet['properties']['title'] 
                                             for sheet in spreadsheet['sheets']]
                            
                            # Create Sheet2 if it doesn't exist
                            if 'Sheet2' not in existing_sheets:
                                request = {
                                    'requests': [{
                                        'addSheet': {
                                            'properties': {
                                                'title': 'Sheet2'
                                            }
                                        }
                                    }]
                                }
                            service.spreadsheets().batchUpdate(
                                    spreadsheetId=spreadsheet_id,
                                    body=request
                                ).execute()
                            st.info("Created Sheet2")
                        
                            headers = [list(df_export.columns)]  # Get column names as a list
                            data = df_export.values.tolist()     # Get data values as list of lists
                            
                            # Combine headers and data
                            all_values = headers + data
                            
                            # Prepare the request body
                            body = {
                                'values': all_values
                            }

                            # Append the data to the Google Sheet
                            service.spreadsheets().values().append(
                                spreadsheetId=spreadsheet_id,
                                range='Sheet2!A1',
                                valueInputOption='USER_ENTERED',
                                body=body
                            ).execute()
                            st.success("Extraction results uploaded to Google Sheet!")
                    except Exception as e:
                        st.error(f"Error updating Google Sheet: {str(e)}")
                else:
                    st.error("Invalid Google Sheet URL")
            else:
                st.error("Please connect to your Google account first.")
