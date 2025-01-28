import pytest
from askharrison.llm.token_util import get_token_count, clip_text_by_token

def test_get_token_count():
    assert get_token_count("Hello, world!") == 4  # Assuming "Hello, world!" is tokenized into 3 tokens
    assert get_token_count("") == 0
    assert get_token_count(12345) == 2  # Assuming numbers are tokenized into 1 token

def test_clip_text_by_token():
    assert clip_text_by_token("Hello, world!", 3) == "Hello, world"
    assert clip_text_by_token("Hello, world!", 2) == "Hello,"
    assert clip_text_by_token("Hello, world!", 0) == ""
    assert clip_text_by_token("", 5) == ""

if __name__ == '__main__':
    pytest.main()