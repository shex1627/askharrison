from typing import Dict, List, Union, Optional
from pydantic import BaseModel, Field, create_model
from datetime import datetime
import json
from enum import Enum
from askharrison.llmparse.schema_recommender import SchemaGenerator
from askharrison.llm.token_util import get_token_count

class ParsingConfig(BaseModel):
    max_chunk_size: int = Field(default=4000, description="Maximum tokens per LLM call")
    batch_strategy: str = Field(default="truncate", description="Strategy for large docs: truncate/batch")
    combine_outputs: bool = Field(default=True, description="Whether to combine multiple outputs")

class DocumentParser:
    """
    Parses documents using either schema dictionary or natural language description.
    
    Example usage:
        # Using schema dictionary
        schema_dict = {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "answer": {"type": "string"}
            }
        }
        parser.parse_document(document, schema_dict)
        
        # Using description
        parser.parse_document(document, "Extract questions and answers from this FAQ")
    """
    
    def __init__(self, llm_client, config: ParsingConfig = ParsingConfig()):
        self.llm_client = llm_client
        self.config = config
        self.schema_generator = SchemaGenerator(llm_client)

    def parse_document(self, 
                      document: str, 
                      schema: Union[Dict, str]) -> Union[Dict, List[Dict]]:
        """
        Parse document using either schema dictionary or description.
        
        Args:
            document: Text document to parse
            schema: Either JSON schema dictionary or natural language description
            
        Returns:
            Parsed data as dictionary or list of dictionaries
        """
        # Convert description to schema if needed
        #if isinstance(schema, str):
        #    schema = self.schema_generator.generate_schema_from_description(schema)
            
        # Handle large documents
        if get_token_count(document) > self.config.max_chunk_size:
            return self._handle_large_document(document, schema)
        
        return self._parse_chunk(document, schema)

    def _handle_large_document(self, 
                             document: str, 
                             schema: Union[Dict, str]) -> Union[Dict, List[Dict]]:
        """Handle documents larger than max chunk size"""
        if self.config.batch_strategy == "truncate":
            return self._parse_chunk(
                document[:self.config.max_chunk_size], 
                schema
            )
        
        # Batch processing
        chunks = self._split_document(document)
        results = [self._parse_chunk(chunk, schema) for chunk in chunks]
        
        if self.config.combine_outputs:
            return self._combine_results(results)
        return results

    def _parse_chunk(self, chunk: str, schema: Union[Dict, str]) -> Dict:
        """Parse a single chunk of text"""
        prompt = self._create_parsing_prompt(chunk, schema)
        response = self.llm_client.generate(prompt)
        return self._parse_response(response)

    def _create_parsing_prompt(self, chunk: str, schema: Union[Dict, str]) -> str:
        """Create parsing prompt from schema"""
        # Convert schema to natural description for better prompting
        # fields = schema.get("properties", {})
        # fields_desc = "\n".join([
        #     f"- {field_name}: {props.get('description', '')}"
        #     for field_name, props in fields.items()
        # ])
        if isinstance(schema, dict):
            fields = schema.get("properties", {})
            fields_desc = "\n".join([
                f"- {field_name}: {props.get('description', '')}"
                for field_name, props in fields.items()
            ])
        else:
            fields_desc = schema

        return f"""
        Extract information from the following text according to this structure:
        {fields_desc}

        Text:
        {chunk}

        Provide the output in JSON format with the specified fields.
        Include only the JSON output, no additional text.
        """

    def _split_document(self, document: str) -> List[str]:
        """Split document into chunks for batch processing"""
        # Simple splitting by max chunk size
        chunks = []
        current_pos = 0
        
        while current_pos < len(document):
            chunk_end = current_pos + self.config.max_chunk_size
            
            # Try to find a good breaking point (newline, period, etc.)
            if chunk_end < len(document):
                # Look for natural break points
                break_points = [
                    document.rfind("\n\n", current_pos, chunk_end),
                    document.rfind(". ", current_pos, chunk_end),
                    document.rfind("\n", current_pos, chunk_end)
                ]
                
                # Use the latest viable break point
                break_point = max(point for point in break_points if point != -1)
                if break_point != -1:
                    chunk_end = break_point
            
            chunks.append(document[current_pos:chunk_end])
            current_pos = chunk_end
            
        return chunks

    def _combine_results(self, results: List[Dict]) -> Dict:
        """Combine multiple parsing results into one"""
        # Basic combination strategy - merge lists and take latest non-list values
        combined = {}
        
        for result in results:
            for key, value in result.items():
                if isinstance(value, list):
                    if key not in combined:
                        combined[key] = []
                    combined[key].extend(value)
                else:
                    combined[key] = value
        
        return combined

    def _parse_response(self, response: str) -> Dict:
        """Parse LLM response into dictionary"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Add fallback parsing if needed
            #raise ValueError("Invalid JSON in LLM response")
            print("Invalid JSON in LLM response, returning raw response")
            return response