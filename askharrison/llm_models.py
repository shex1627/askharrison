import requests
import pandas as pd
from typing import List, Dict, Any
from openai import OpenAI
import pandas as pd
import re
from typing import Any

def process_question(question, model='gpt-4o'):
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

def polish_code(code: str) -> str:
    """
    Polish the code by removing the leading "python" or "py",  \
    removing surrounding '`' characters  and removing trailing spaces and new lines.

    Args:
        code (str): A string of Python code.

    Returns:
        str: Polished code.

    """
    if re.match(r"^(python|py)", code):
        code = re.sub(r"^(python|py)", "", code)
    if re.match(r"^`.*`$", code):
        code = re.sub(r"^`(.*)`$", r"\1", code)
    code = code.strip()
    return code

def extract_python_code(response: str, separator: str = "```") -> str:
    """
    Extract the code from the llm response.

    Args:
        response (str): Response
        separator (str, optional): Separator. Defaults to "```".

    Raises:
        NoCodeFoundError: No code found in the response

    Returns:
        str: Extracted code from the response

    """
    code = response

    # If separator is in the response then we want the code in between only
    if separator in response and len(code.split(separator)) > 1:
        code = code.split(separator)[1]
    code = polish_code(code)

    return code

def safe_eval(input_str: str, default_output: Any=None):
    try:
        return eval(input_str)
    except:
        return default_output