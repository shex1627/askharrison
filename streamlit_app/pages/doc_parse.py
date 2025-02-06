import streamlit as st
from askharrison.llmparse.schema_recommender import SchemaGenerator
from askharrison.llm.openai_llm_client import OpenAIClient
from askharrison.llm_models import extract_python_code, safe_eval
from askharrison.llmparse.document_parser import DocumentParser
import json
import tempfile
import os

st.set_page_config(page_title="Document Parser", layout="wide")

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'schema' not in st.session_state:
    st.session_state.schema = None
if 'parsed_doc' not in st.session_state:
    st.session_state.parsed_doc = None

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

# Sidebar for API key configuration
with st.sidebar:
    st.title("Configuration")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    if api_key:
        st.session_state.api_key = api_key
        if initialize_clients():
            st.success("API key configured successfully!")

# Main content area
st.title("Document Parser")

# File upload section
uploaded_file = st.file_uploader("Upload a document", type=['txt', 'pdf', 'docx'])
if uploaded_file and st.session_state.api_key:
    file_path = save_uploaded_file(uploaded_file)
    with open(file_path, 'r', encoding='utf-8') as f:
        document_content = f.read()
    
    # Chat interface for schema configuration
    st.header("Schema Configuration Chat")
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Describe the structure you want to extract from the document"):
        # Add user message to chat
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Generate schema based on user input
        parsed_output = None
        try:
            recommended_schema = st.session_state.schema_generator.recommend_schema_from_document(document_content)
            schema_dict = recommended_schema
            from askharrison.llmparse.uitl import format_json_schema
            print(format_json_schema(schema_dict))
            st.session_state.schema = schema_dict
            
            # Add assistant response to chat
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"Generated schema:\n```json\n{json.dumps(schema_dict, indent=2)}\n```"
            })
            
            # Parse document with schema
            parsed_output = st.session_state.document_parser.parse_document(document_content, schema_dict)
            if parsed_output:
                st.session_state.parsed_doc = parsed_output
        except Exception as e:
            import traceback
            # use traceback to get the error message, and display it
            trace_info = traceback.format_exc()
            st.error(f"Error generating schema: {str(e)}, {trace_info}")
            if parsed_output:
                st.error(f"Error parsing document: {parsed_output}")
    
    # Display and download parsed results
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
                "Download Parsed Document (JSON)",
                data=json.dumps(st.session_state.parsed_doc, indent=2),
                file_name="parsed_document.json",
                mime="application/json"
            )

# Clear session state button
if st.sidebar.button("Clear Session"):
    for key in ['api_key', 'chat_messages', 'schema', 'parsed_doc']:
        if key in st.session_state:
            del st.session_state[key]
    st.sidebar.success("Session cleared!")
    st.experimental_rerun()

# Instructions
if not st.session_state.api_key:
    st.info("Please enter your OpenAI API key in the sidebar to get started.")
elif not uploaded_file:
    st.info("Please upload a document to begin parsing.")