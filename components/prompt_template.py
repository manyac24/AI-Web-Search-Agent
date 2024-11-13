import streamlit as st
import pandas as pd
from utils.search_results import render_search_execution

def validate_prompt_template(template, placeholder):
    """Validate if the prompt template contains the correct placeholder"""
    if not template:
        return False, "Prompt template cannot be empty"
    if '{' + placeholder + '}' not in template:
        return False, f"Template must contain the placeholder {{{placeholder}}}"
    return True, "Valid template"

def generate_preview_queries(df, column, template, num_previews=5):
    """Generate preview queries using the template and data"""
    if df is None or column not in df.columns:
        return []
    
    preview_data = df[column].head(num_previews)
    queries = []
    for value in preview_data:
        query = template.replace('{' + column + '}', str(value))
        queries.append({'entity': value, 'query': query})
    return queries

def render_prompt_template_section(df, selected_column):
    """Render the prompt template section of the dashboard"""
    st.header("Define Your Query Template")
   
    # Create columns for template input and helper buttons
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt_template = st.text_area(
            "Enter your prompt template",
            value=st.session_state.prompt_template,
            help=f"Use {{{selected_column}}} as a placeholder for each entity in a column",
            height=100
        )
    # Validate template and show preview
    if prompt_template:
        is_valid, message = validate_prompt_template(prompt_template, selected_column)
        
        if is_valid:
            st.success("✓ Valid template")
            st.session_state.prompt_template = prompt_template
            
            # Generate and display preview queries
            st.subheader("Preview Queries")
            queries = generate_preview_queries(df, selected_column, prompt_template)
            
            if queries:
                preview_df = pd.DataFrame(queries)
                st.dataframe(preview_df, use_container_width=True)

            render_search_execution(selected_column)    
        else:
            st.error(message)