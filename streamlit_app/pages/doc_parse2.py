import streamlit as st
from askharrison.llmparse.schema_recommender import SchemaGenerator
from askharrison.llm.openai_llm_client import OpenAIClient
from askharrison.llm.token_util import clip_text_by_token
from askharrison.llmparse.document_parser import DocumentParser, ParsingConfig
import json
import tempfile
import os

st.set_page_config(page_title="Interactive Document Parser", layout="wide")

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'schema' not in st.session_state:
    st.session_state.schema = None
if 'document_content' not in st.session_state:
    st.session_state.document_content = None
if 'parsed_doc' not in st.session_state:
    st.session_state.parsed_doc = None
if 'preview_tokens' not in st.session_state:
    st.session_state.preview_tokens = 1000

def initialize_clients():
    if st.session_state.api_key:
        try:
            openai_client = OpenAIClient(api_key=st.session_state.api_key)
            st.session_state.schema_generator = SchemaGenerator(openai_client)
            st.session_state.document_parser = DocumentParser(openai_client)
            return True
        except Exception as e:
            st.error(f"Error initializing clients: {str(e)}")
            return False
    return False

def save_uploaded_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name

# Sidebar for configuration
with st.sidebar:
    st.title("Configuration")
    
    # API Key input
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    if api_key:
        st.session_state.api_key = api_key
        if initialize_clients():
            st.success("API key configured successfully!")
    
    # Preview token adjustment
    st.session_state.preview_tokens = st.slider(
        "Preview Token Length", 
        min_value=100, 
        max_value=5000, 
        value=st.session_state.preview_tokens
    )
    
    # Clear session button
    if st.button("Clear Session"):
        for key in ['api_key', 'chat_messages', 'schema', 'document_content', 'parsed_doc']:
            if key in st.session_state:
                del st.session_state[key]
        st.success("Session cleared!")
        st.experimental_rerun()

# Main content area
st.title("Interactive Document Parser")

# File upload section
uploaded_file = st.file_uploader("Upload a document", type=['txt', 'pdf', 'docx'])
if uploaded_file and st.session_state.api_key:
    file_path = save_uploaded_file(uploaded_file)
    with open(file_path, 'r', encoding='utf-8') as f:
        st.session_state.document_content = f.read()
    
    # Document preview section
    st.header("Document Preview")
    preview_expander = st.expander("Show Document Preview")
    with preview_expander:
        preview_text = clip_text_by_token(
            st.session_state.document_content, 
            st.session_state.preview_tokens
        )
        st.text_area("Preview", preview_text, height=200)
    
    # Schema section
    st.header("Schema Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get Recommended Schema"):
            try:
                recommended_schema = st.session_state.schema_generator.recommend_schema_from_document(
                    st.session_state.document_content
                )
                st.session_state.schema = recommended_schema
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": "Generated initial schema recommendation."
                })
            except Exception as e:
                st.error(f"Error generating schema: {str(e)}")
    
    # Schema display and editing
    if st.session_state.schema:
        schema_json = json.dumps(st.session_state.schema, indent=2)
        edited_schema = st.text_area(
            "Edit Schema (JSON)", 
            schema_json,
            height=300
        )
        try:
            st.session_state.schema = json.loads(edited_schema)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {str(e)}")
    
        # Schema feedback chat
        st.header("Schema Refinement Chat")
        
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input for schema feedback
        if feedback := st.chat_input("Provide feedback to refine the schema"):
            st.session_state.chat_messages.append({"role": "user", "content": feedback})
            try:
                updated_schema = st.session_state.schema_generator.update_schema_from_feedback(
                    st.session_state.schema,
                    feedback
                )
                st.session_state.schema = updated_schema
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"Updated schema based on feedback:\n```json\n{json.dumps(updated_schema, indent=2)}\n```"
                })
                print("Updated schema:")
                print(updated_schema)
            except Exception as e:
                st.error(f"Error updating schema: {str(e)}")
        
        # Parsing section
        st.header("Document Parsing")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Parse Document"):
                try:
                    parsed_output = st.session_state.document_parser.parse_document(
                        st.session_state.document_content,
                        st.session_state.schema
                    )
                    st.session_state.parsed_doc = parsed_output
                except Exception as e:
                    st.error(f"Error parsing document: {str(e)}")
        
        with col2:
            if st.button("Parse Preview"):
                try:
                    print(f"Parsing preview with tokens: {st.session_state.preview_tokens}")
                    print(f"Parsing schema: {st.session_state.schema}")
                    preview_text = clip_text_by_token(
                        st.session_state.document_content,
                        st.session_state.preview_tokens
                    )
                    parsed_preview = st.session_state.document_parser.parse_document(
                        preview_text,
                        st.session_state.schema
                    )
                    st.session_state.parsed_doc = parsed_preview
                except Exception as e:
                    st.error(f"Error parsing preview: {str(e)}")
        
        # Display parsing results
        if st.session_state.parsed_doc:
            st.header("Parsed Results")
            st.json(st.session_state.parsed_doc)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download Schema (JSON)",
                    data=json.dumps(st.session_state.schema, indent=2),
                    file_name="schema.json",
                    mime="application/json"
                )
            with col2:
                st.download_button(
                    "Download Parsed Results (JSON)",
                    data=json.dumps(st.session_state.parsed_doc, indent=2),
                    file_name="parsed_results.json",
                    mime="application/json"
                )

# Instructions
if not st.session_state.api_key:
    st.info("Please enter your OpenAI API key in the sidebar to get started.")
elif not uploaded_file:
    st.info("Please upload a document to begin parsing.")