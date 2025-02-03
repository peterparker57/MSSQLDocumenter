import anthropic
import json
import os
from typing import Dict, Any, Optional
import logging
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        """Initialize the LLM client."""
        with open('src/python/llm_config.json', 'r') as f:
            self.config = json.load(f)
            
        self.default_provider = self.config.get('default_provider', 'anthropic')
        self.clients = {}
        
        # Initialize Anthropic client if configured
        if 'anthropic' in self.config['providers']:
            anthropic_config = self.config['providers']['anthropic']
            api_key = anthropic_config.get('api_key') or os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.clients['anthropic'] = anthropic.Anthropic(api_key=api_key)
        
        # Initialize Ollama client if configured
        if 'ollama' in self.config['providers']:
            logger.info("Initializing Ollama client...")
            self.clients['ollama'] = OllamaClient(self.config['providers']['ollama'])
            
        if not self.clients:
            raise ValueError("No LLM providers configured")
            
    def get_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for specified provider."""
        provider = provider or self.default_provider
        return self.config['providers'].get(provider, {})
            
    async def test_connection(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Test the LLM connection."""
        provider = provider or self.default_provider
        try:
            logger.info(f"Testing LLM connection with provider: {provider}")
            
            if provider not in self.clients:
                raise ValueError(f"Provider {provider} not configured")
                
            client = self.clients[provider]
            
            if provider == 'anthropic':
                config = self.get_provider_config(provider)
                response = client.messages.create(
                    model=config.get('model', 'claude-3-opus-20240229'),
                    max_tokens=100,
                    messages=[{
                        "role": "user",
                        "content": "Say hello!"
                    }]
                )
                return {
                    "provider": provider,
                    "model": response.model,
                    "response": response.content[0].text
                }
            elif provider == 'ollama':
                return await client.test_connection()
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"LLM test failed: {str(e)}")
            raise
            
    async def generate_response(self, prompt: str, provider: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        provider = provider or self.default_provider
        config = self.get_provider_config(provider)
        
        try:
            if provider == 'anthropic':
                response = self.clients['anthropic'].messages.create(
                    model=config.get('model', 'claude-3-opus-20240229'),
                    max_tokens=config.get('max_tokens', 1000),
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.content[0].text
            elif provider == 'ollama':
                return await self.clients['ollama'].generate(prompt)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise
            
    async def analyze_table(self, doc: str, provider: Optional[str] = None) -> str:
        """Analyze table structure and generate documentation."""
        prompt = f"""Analyze this SQL Server table structure and provide a clear, technical description:

{doc}

Please provide:
1. A brief overview of the table's purpose
2. Key structural features (primary key, important columns)
3. Relationships with other tables
4. Any performance considerations
"""
        return await self.generate_response(prompt, provider)
            
    async def analyze_view(self, doc: str, provider: Optional[str] = None) -> str:
        """Analyze view definition and generate documentation."""
        prompt = f"""Analyze this SQL Server view definition and provide a clear, technical description:

{doc}

Please provide:
1. A brief overview of the view's purpose
2. The main tables/views it references
3. Any important transformations or calculations
4. Usage considerations
"""
        return await self.generate_response(prompt, provider)
            
    async def analyze_procedure(self, doc: str, provider: Optional[str] = None) -> str:
        """Analyze stored procedure and generate documentation."""
        prompt = f"""Analyze this SQL Server stored procedure and provide a clear, technical description:

{doc}

Please provide:
1. A brief overview of the procedure's purpose
2. Description of input/output parameters
3. Key operations and logic flow
4. Important tables affected
5. Any performance considerations
"""
        return await self.generate_response(prompt, provider)
            
    async def analyze_function(self, doc: str, provider: Optional[str] = None) -> str:
        """Analyze function and generate documentation."""
        prompt = f"""Analyze this SQL Server function and provide a clear, technical description:

{doc}

Please provide:
1. A brief overview of the function's purpose
2. Description of parameters and return value
3. Key calculations or operations
4. Usage considerations
"""
        return await self.generate_response(prompt, provider)

    async def analyze_search_intent(self, query: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """Analyze search query to determine intent."""
        try:
            prompt = f"""Analyze this database search query: "{query}"
            
            Determine:
            1. What type of database objects is the user interested in? (tables, views, procedures, functions, or any)
            2. What level of detail does the user want? (names_only, basic_info, or full_details)
            3. What specific information should be included in the response?
            4. How should the results be formatted?
            
            Return your analysis as a JSON object with these fields:
            - object_type: "table", "view", "procedure", "function", or "any"
            - detail_level: "names_only", "basic_info", or "full_details"
            - include_fields: array of specific fields to include
            - format_template: string showing how each result should be formatted
            - search_query: the actual search query to use (simplified if needed)
            
            Example responses:
            For "list all tables":
            {
                "object_type": "table",
                "detail_level": "names_only",
                "include_fields": ["schema", "name"],
                "format_template": "{schema}.{name}",
                "search_query": "tables"
            }
            
            For "show me the customer table":
            {
                "object_type": "table",
                "detail_level": "full_details",
                "include_fields": ["schema", "name", "columns", "indexes", "foreign_keys"],
                "format_template": "Table: {schema}.{name}\n\nColumns:\n{columns}\n\nIndexes:\n{indexes}\n\nForeign Keys:\n{foreign_keys}",
                "search_query": "customer table"
            }"""

            response = await self.generate_response(prompt, provider)
            
            # Find the first { and last } to extract just the JSON part
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                try:
                    intent = json.loads(json_str)
                    logger.info(f"Successfully parsed search intent: {intent}")
                    return intent
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.error(f"Raw response: {response}")
            
            # Return default intent if parsing fails
            return {
                "object_type": "any",
                "detail_level": "basic_info",
                "include_fields": ["schema", "name", "type"],
                "format_template": "{schema}.{name} ({type})",
                "search_query": query
            }
            
        except Exception as e:
            logger.error(f"Error analyzing search intent: {str(e)}")
            # Return default intent on error
            return {
                "object_type": "any",
                "detail_level": "basic_info",
                "include_fields": ["schema", "name", "type"],
                "format_template": "{schema}.{name} ({type})",
                "search_query": query
            }