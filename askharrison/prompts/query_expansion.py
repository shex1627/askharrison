def generate_search_queries_prompt(problem_statement: str, num_queries: int=10, search_engine="google") -> str:
    prompt = f"""generate {num_queries} {search_engine} search queries only including plain text without any advanced querying macros, strategize the search query you make to increase chance of finding relevant results 
#### problem statement:
{problem_statement}

#### output:
return a python list of strings, each string is a search query
"""
    return prompt