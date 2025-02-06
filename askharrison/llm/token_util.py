import tiktoken
from typing import Any

enc = tiktoken.get_encoding("cl100k_base")

def get_token_count(obj: Any) -> int:
    return len(enc.encode(str(obj)))

def clip_text_by_token(text: str, max_tokens: int) -> str:
    token_count = get_token_count(text)
    if token_count <= max_tokens:
        return text
    else:
        return enc.decode(enc.encode(text)[:max_tokens])
    
def split_documents(text: str, max_tokens: int, overlap: int = 100) -> list[str]:
    """Split text into chunks of max_tokens with optional overlap."""
    if get_token_count(text) <= max_tokens:
        return [text]
    
    # Get all tokens
    tokens = enc.encode(text)
    chunks = []
    start = 0
    
    while start < len(tokens):
        # Get chunk of max_tokens
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        
        # Decode chunk back to text
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        # Move start position, accounting for overlap
        start = end - overlap
        
    return chunks