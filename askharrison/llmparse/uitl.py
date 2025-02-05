def format_json_schema(schema, indent=0, parent_key=None):
    """
    Format a JSON schema dictionary into a more readable string representation.
    
    Args:
        schema (dict): The JSON schema dictionary
        indent (int): Current indentation level
        parent_key (str): Key from parent object for context
    
    Returns:
        str: Formatted string representation of the schema
    """
    output = []
    indent_str = "  " * indent
    
    # Handle type definitions
    if "type" in schema:
        type_str = schema["type"]
        desc = f"{schema.get('description', '')}"
        title = f"{schema.get('title', parent_key if parent_key else 'Root')}"
        
        # Start with the title
        output.append(f"{indent_str}{title}:")
        
        # Add type and description
        output.append(f"{indent_str}  Type: {type_str}")
        if desc:
            output.append(f"{indent_str}  Description: {desc}")
            
        # Handle additional type-specific properties
        if type_str == "object" and "properties" in schema:
            output.append(f"{indent_str}  Properties:")
            for prop_name, prop_schema in schema["properties"].items():
                prop_lines = format_json_schema(prop_schema, indent + 2, prop_name)
                output.extend(prop_lines)
                
            # Add required fields if present
            if "required" in schema:
                output.append(f"{indent_str}  Required fields: {', '.join(schema['required'])}")
                
        elif type_str == "array" and "items" in schema:
            output.append(f"{indent_str}  Array items:")
            item_lines = format_json_schema(schema["items"], indent + 2)
            output.extend(item_lines)
            
        # Handle constraints
        constraints = []
        if "minimum" in schema:
            constraints.append(f"minimum: {schema['minimum']}")
        if "maximum" in schema:
            constraints.append(f"maximum: {schema['maximum']}")
        if "minLength" in schema:
            constraints.append(f"min length: {schema['minLength']}")
        if "maxLength" in schema:
            constraints.append(f"max length: {schema['maxLength']}")
        if "pattern" in schema:
            constraints.append(f"pattern: {schema['pattern']}")
        if "enum" in schema:
            constraints.append(f"allowed values: {schema['enum']}")
            
        if constraints:
            output.append(f"{indent_str}  Constraints: {', '.join(constraints)}")
            
    return output
