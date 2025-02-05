from typing import Dict, List, Union, Optional
from pydantic import BaseModel, Field, create_model
from datetime import datetime
from abc import ABC, abstractmethod
import json
from enum import Enum

from askharrison.llm.token_util import clip_text_by_token, get_token_count
from askharrison.llm_models import extract_python_code, safe_eval

# Base Schema Models
class BaseOutputSchema(BaseModel):
    """Base class for all output schemas"""
    raw_text: str = Field(description="Original text that generated this output")
    extracted_at: datetime = Field(default_factory=datetime.now)

class FAQSchema(BaseOutputSchema):
    question: str = Field(description="The main question being asked")
    answer: str = Field(description="The answer provided")
    resolution_status: Optional[str] = Field(default=None, description="Resolution status if applicable")
    confidence_score: float = Field(default=1.0, description="LLM confidence in extraction")

class ResumeSchema(BaseOutputSchema):
    basic_info: Dict[str, str] = Field(description="Basic information like name, contact, etc.")
    skills: List[str] = Field(description="List of skills")
    work_experience: List[Dict] = Field(description="List of work experiences")
    education: List[Dict] = Field(description="List of education entries")
    
class SupportTicketSchema(BaseOutputSchema):
    issue: str = Field(description="Main issue description")
    category: str = Field(description="Issue category")
    status: str = Field(description="Current status")
    resolution: Optional[str] = Field(default=None, description="Resolution if available")

class ParsingConfig(BaseModel):
    max_chunk_size: int = Field(default=10000, description="Maximum tokens per LLM call")
    output_format: str = Field(default="json", description="Output format (json/dict)")
    batch_strategy: str = Field(default="truncate", description="Strategy for large docs: truncate/batch")
    combine_outputs: bool = Field(default=True, description="Whether to combine multiple outputs")

class SchemaGenerator:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self._schema_registry = {
            "faq": FAQSchema,
            "resume": ResumeSchema,
            "support_ticket": SupportTicketSchema
        }
        self.message_history = []

    def clear_message_history(self):
        self.message_history = []
    
    def _create_schema_generation_prompt(self, description: str) -> str:
        return f"""
        Convert the following natural language description into a structured schema.
        Make reasonable assumptions about fields that might be useful.
        
        Description: {description}
        
        Generate a JSON schema that captures this structure. Include:
        1. All explicitly mentioned fields
        2. Common/useful fields for this type of data
        3. Appropriate data types for each field
        
        Output the schema in valid JSON format.
        """
    
    def recommend_schema_from_document(self, document: str, max_tokens: int=5000) -> Dict:
        """
        Analyzes document content and recommends a parsing schema with explanation.
        Returns both schema and natural language description.
        """
        document_trunct = clip_text_by_token(document, max_tokens)
        prompt = f"""
        Analyze the following document and suggest:
        1. A natural language description of how to structure this data
        2. A JSON schema for parsing similar documents
        
        Document:
        {document_trunct}...  # Using first {max_tokens} tokens for analysis

        Output the schema in valid JSON format.
        example output:
        {{
            "description": "<your description>",
            "schema": {{
                "field1": "type1",
                "field2": "type2",
                ...
            }}
        }}
        """
        response = self.llm_client.generate(prompt)
        schema = safe_eval(extract_python_code(response))
        if not schema:
            return response
        self.message_history.append({"role": "user", "content": document})
        self.message_history.append({"role": "assistant", "content": schema})
        return schema

    def generate_schema_from_description(self, description: str) -> BaseModel:
        """
        Converts a natural language description into a Pydantic model.
        """
        prompt = self._create_schema_generation_prompt(description)
        response = self.llm_client.generate(prompt)
        schema_dict = safe_eval(extract_python_code(response))
        if not schema_dict:
            return response
        self.message_history.append({"role": "user", "content": description})
        self.message_history.append({"role": "assistant", "content": schema_dict})
        return schema_dict #self._create_pydantic_model(schema_dict)
    
    def update_schema_from_feedback(self, schema: BaseModel, feedback: str, last_n:int=3) -> BaseModel:
        """
        Updates the schema based on user feedback.
        """
        context = []
        if self.message_history:
            # use last n messages as context
            context.append(self.message_history[:-last_n])
        #context = "\n".join([f"{m['role']}: {m['content']}" for m in context])
        prompt = f"""
        Given the schema: {schema} and feedback: {feedback}, 
        suggest improvements to the schema.
        Output the updated schema in valid JSON format.
        #### conversation history:
        {context}
        #### example output:
        {{
            "description": "<your description>",
            "schema": {{
                "field1": "type1",
                "field2": "type2",
                ...
            }}
        }}
        """
        response = self.llm_client.generate(prompt)
        updated_schema_dict = safe_eval(extract_python_code(response))
        if not updated_schema_dict:
            return response
        self.message_history.append({"role": "user", "content": feedback})
        self.message_history.append({"role": "assistant", "content": updated_schema_dict})
        return updated_schema_dict