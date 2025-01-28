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