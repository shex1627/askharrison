import requests
import pandas as pd
from typing import List, Dict, Any, Callable
from openai import OpenAI
import pandas as pd
import re
import concurrent.futures
import time
import random
from tqdm import tqdm
import functools
import tiktoken

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

def parallel_llm_processor(prompts: List[str], 
                           llm_function: Callable[[str], Any], 
                           max_workers: int = 5):
    """
    Process a list of LLM prompts in parallel, submitting each prompt individually.
    Displays a progress bar using tqdm.
    
    :param prompts: List of prompts to process
    :param llm_function: Function to call for each prompt
    :param max_workers: Maximum number of parallel workers
    :return: List of results from LLM processing
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all prompts to the executor
        future_to_prompt = {executor.submit(llm_function, prompt): prompt for prompt in prompts}
        
        # Use tqdm to create a progress bar
        with tqdm(total=len(prompts), desc="Processing prompts") as pbar:
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_prompt):
                prompt = future_to_prompt[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"An error occurred while processing prompt: {prompt[:30]}...")
                    print(f"Error: {str(e)}")
                finally:
                    pbar.update(1)  # Update the progress bar
    
    return results

def chunk_llm_input(max_tokens: int, encoding_name: str = "cl100k_base"):
    """
    Decorator to chunk input into smaller pieces based on token count before passing it to the decorated function.

    :param max_tokens: Maximum number of tokens allowed in each chunk
    :param encoding_name: Name of the encoding to use
    :return: Decorator function

    # Example usage:
    @chunk_llm_input(max_tokens=2048)
    def generate_llm_prompt(objects: List[str]) -> str:
        prompt = "Summarize the following items:\n\n"
        for obj in objects:
            prompt += f"- {obj}\n"
        return prompt
        
    results = process_chunked(objects)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(objects: List[Any], *args, **kwargs):
            encoding = tiktoken.get_encoding(encoding_name)
            
            def get_token_count(obj: Any) -> int:
                return len(encoding.encode(str(obj)))
            
            chunks = []
            current_chunk = []
            current_token_count = 0
            
            for obj in objects:
                if isinstance(obj, str):
                    obj_token_count = get_token_count(obj)
                else:
                    obj_token_count = get_token_count(str(obj))
                print(obj_token_count)
                
                if current_token_count + obj_token_count > max_tokens:
                    chunks.append(current_chunk)
                    current_chunk = [obj]
                    current_token_count = obj_token_count
                else:
                    current_chunk.append(obj)
                    current_token_count += obj_token_count
            
            if current_chunk:
                chunks.append(current_chunk)
            
            results = []
            for chunk in chunks:
                result = func(chunk, *args, **kwargs)
                results.append(result)
            
            return results
        
        return wrapper
    
    return decorator