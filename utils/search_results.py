import streamlit as st
from components.prompt_template import *
import hashlib
import sqlite3
import json
import concurrent.futures
from ratelimit import limits, sleep_and_retry
from datetime import datetime
from serpapi import GoogleSearch
from utils.llm_processing import render_extraction_by_LLM


# with open("config.json") as f:
#     config = json.load(f)
# SERPAPI_KEY = config["SERPAPI_KEY"]
SERPAPI_KEY=st.secrets["SERPAPI_KEY"]

class SearchResultsManager:
    def __init__(self, db_path="search_results.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize SQLite database for storing search results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_results (
                    query_hash TEXT PRIMARY KEY,
                    entity TEXT,
                    query TEXT,
                    results TEXT,
                    timestamp DATETIME
                )
            """)
    
    def get_results(self, entity, query):
        """Retrieve cached results for a query"""
        query_hash = self._generate_hash(entity, query)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT results FROM search_results WHERE query_hash = ?",
                (query_hash,)
            )
            result = cursor.fetchone()
            return json.loads(result[0]) if result else None
    
    def store_results(self, entity, query, results):
        """Store search results in the database"""
        query_hash = self._generate_hash(entity, query)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO search_results 
                (query_hash, entity, query, results, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (query_hash, entity, query, json.dumps(results), datetime.now())
            )
    
    def _generate_hash(self, entity, query):
        """Generate a unique hash for entity-query combination"""
        return hashlib.md5(f"{entity}:{query}".encode()).hexdigest()

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
@sleep_and_retry
@limits(calls=100, period=60)
def search_with_serpapi(query):
    """Perform a search using SerpAPI with rate limiting"""
    try:
        search = GoogleSearch({
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 5  # Limit to top 5 results per query
        })
        results = search.get_dict()
        
        # Extract relevant information from results
        organic_results = results.get('organic_results', [])
        structured_results = []
        
        for result in organic_results:
            structured_results.append({
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'position': result.get('position', 0)
            })
        
        return structured_results
    
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []
    
def process_batch_searches(entities_queries, results_manager):
    """Process a batch of searches with concurrent execution"""
    processed_results = []
    
    def process_single_search(entity, query):
        # Check cache first
        cached_results = results_manager.get_results(entity, query)
        if cached_results:
            return {'entity': entity, 'query': query, 'results': cached_results, 'cached': True}
        
        # Perform new search if not cached
        results = search_with_serpapi(query)
        results_manager.store_results(entity, query, results)
        return {'entity': entity, 'query': query, 'results': results, 'cached': False}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        future_to_search = {
            executor.submit(
                process_single_search, 
                item['entity'], 
                item['query']
            ): item for item in entities_queries
        }
        
        for future in concurrent.futures.as_completed(future_to_search):
            try:
                result = future.result()
                processed_results.append(result)
            except Exception as e:
                st.error(f"Error processing search: {str(e)}")
    
    return processed_results


def render_search_execution(selected_column):
     # Initialize search results manager
        results_manager = SearchResultsManager()
                
        # Generate queries for all entities
        all_queries = generate_preview_queries(
            st.session_state.df,
            selected_column,
            st.session_state.prompt_template,
            num_previews=len(st.session_state.df)
        )
        
        if st.button("Execute Web Search"):
            with st.spinner("Performing web searches..."):
                # Process searches in batches
                search_results = []
                for i in range(0, len(all_queries), 10):
                    batch = all_queries[i:i + 10]
                    batch_results = process_batch_searches(batch, results_manager)
                    search_results.extend(batch_results)
                    
                    # Update progress
                    progress = (i + len(batch)) / len(all_queries)
                    st.progress(progress)
                
                # Store results in session state
                st.session_state.search_results = search_results
                st.success(f"Completed searches for {len(search_results)} entities!")
        
    
        if hasattr(st.session_state, 'search_results'):            
            # Get LLM configuration
            render_extraction_by_LLM()
           
