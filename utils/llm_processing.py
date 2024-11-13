import streamlit as st
import re
from groq import AsyncGroq
import asyncio
from typing import List, Dict
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from components.extraction_result import render_extraction_results

with open("config.json") as f:
    config = json.load(f)
groq_api_key= config["GROQ_API_KEY"]

def replace_with_entity(text):
    # Use regex to replace anything between curly braces with 'entity'
    return re.sub(r"\{.*?\}", "{entity}", text)

OPENAI_API_KEY="your_openai_key_here"
class LLMProcessor:
    def __init__(self,  model=None):
        self.model = model or ( 'mixtral-8x7b-32768')
        self.setup_client()
        
    def setup_client(self):
        """Initialize the appropriate LLM client"""
        self.groq_client = AsyncGroq(api_key=groq_api_key)
    
    def create_extraction_prompt(self, entity: str, extraction_template: str, 
                               search_results: List[Dict], context: str = "") -> str:
        """Create a detailed prompt for information extraction"""
        prompt = f"""Task: Extract information about {entity} based on the following search results.
Specific Request: {extraction_template.format(entity=entity)}

Context: {context}

Search Results:
"""
        
        for idx, result in enumerate(search_results, 1):
            prompt += f"\n{idx}. Title: {result['title']}\nURL: {result['link']}\nSnippet: {result['snippet']}\n"
        
        prompt += """\nPlease extract the requested information and provide it in the following JSON format:
{
    "extracted_info": "The specific information requested",
    "confidence": "HIGH/MEDIUM/LOW based on reliability of sources and clarity of information",
    "source_urls": ["list of URLs where information was found"],
    "additional_notes": "Any relevant context or caveats about the extracted information"
}

If the information cannot be found, please indicate this clearly in the response."""
        
        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_single_entity(self, entity: str, extraction_template: str, 
                                  search_results: List[Dict], context: str = "") -> Dict:
        """Process a single entity's search results through the LLM"""
        try:
            prompt = self.create_extraction_prompt(entity, extraction_template, search_results, context)
            
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise information extraction assistant. Extract exactly what is asked for and format it according to the specified JSON structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            result = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                # Fallback parsing if LLM didn't return proper JSON
                parsed_result = {
                    "extracted_info": "Error parsing LLM response",
                    "confidence": "LOW",
                    "source_urls": [],
                    "additional_notes": "Error in JSON formatting from LLM"
                }
            
            return {
                "entity": entity,
                "extraction_result": parsed_result,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "entity": entity,
                "extraction_result": {
                    "extracted_info": f"Error: {str(e)}",
                    "confidence": "LOW",
                    "source_urls": [],
                    "additional_notes": "Error during LLM processing"
                },
                "status": "error"
            }

async def process_batch_with_llm(entities_results: List[Dict], llm_processor: LLMProcessor,
                               extraction_template: str, batch_size: int = 5) -> List[Dict]:
    """Process a batch of entities through the LLM with concurrent execution"""
    all_results = []
    
    for i in range(0, len(entities_results), batch_size):
        batch = entities_results[i:i + batch_size]
        tasks = []
        
        for entity_result in batch:
            task = llm_processor.process_single_entity(
                entity=entity_result['entity'],
                extraction_template=extraction_template,
                search_results=entity_result['results']
            )
            tasks.append(task)
            print (entity_result['entity'])
        
        batch_results = await asyncio.gather(*tasks)
        all_results.extend(batch_results)
        
        # Add a small delay between batches to avoid rate limits
        await asyncio.sleep(1)
    
    return all_results

def render_extraction_configuration():
    """Render the LLM extraction configuration interface"""
    input_text=st.session_state.prompt_template
    extraction_template = replace_with_entity(input_text)
    return {
        'provider': 'groq',
        'model': 'mixtral-8x7b-32768',
        'extraction_template': extraction_template
    }


def render_extraction_by_LLM():
    llm_config = render_extraction_configuration()
                # if st.button("Extract Information"):
    with st.spinner("Processing through LLM..."):
        # Initialize LLM processor
        llm_processor = LLMProcessor(
            model=llm_config['model']
        )
        
        # Process results through LLM
        extraction_results = asyncio.run(
            process_batch_with_llm(
                st.session_state.search_results,
                llm_processor,
                llm_config['extraction_template']
            )
        )
        
        # Store results in session state
        st.session_state.extraction_results = extraction_results
        st.success("Information extraction completed!")
    
    # Display extraction results if available
    if hasattr(st.session_state, 'extraction_results'):
        render_extraction_results(st.session_state.extraction_results)  
