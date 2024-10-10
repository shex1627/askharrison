from collections import defaultdict
import arxiv
from tqdm import tqdm
from askharrison.llm_models import process_question, safe_eval, extract_python_code

def generate_search_queries_prompt(problem_statement: str, num_queries: int=10, search_engine="google") -> str:
    prompt = f"""generate {num_queries} {search_engine} search queries only including plain text without any advanced querying macros, strategize the search query you make to increase chance of finding relevant results 
#### problem statement:
{problem_statement}

#### output:
return a python list of strings, each string is a search query
"""
    return prompt

def generate_diffusion_search_queries_prompt(problem_statement: str, num_queries: int=10, search_engine="google") -> str:
    prompt = f"""generate {num_queries} {search_engine} search queries only including plain text without any advanced querying macros,
    use diversion thinking, looking at the problem from a different perspectives and angles but still able to bring back the insights to the original problem
#### problem statement:
{problem_statement}

#### output:
return a python list of strings, each string is a search query
"""
    return prompt

def generate_search_queries(problem_statement: str, num_queries: int, search_engine: str, model="gpt-4") -> list[str]:
    """
    Expand a query using LLM and return a list of queries
    """
    prompt = generate_search_queries_prompt(problem_statement, num_queries, search_engine)
    queries_llm_output = process_question(prompt, model=model)
    queries = safe_eval(extract_python_code(queries_llm_output))
    return queries

def generate_diffusion_search_queries(problem_statement: str, num_queries: int, search_engine: str, model="gpt-4") -> list[str]:
    """
    Expand a query using LLM and return a list of queries
    """
    prompt = generate_diffusion_search_queries_prompt(problem_statement, num_queries, search_engine)
    queries_llm_output = process_question(prompt, model=model)
    queries = safe_eval(extract_python_code(queries_llm_output))
    return queries