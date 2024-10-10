def create_arxiv_filtering_prompt(problem_statement: str, doc_abstract: str):
    # check if the problem statement is in the abstract
    prompt = f"""return parts of the abstracts that directly address the problem statement, none if abtracts does not directly address the problem statement. return nothing even if the abstracts address the problem statement but not directly

    Problem Statement: {problem_statement}
    Document Abstract: {doc_abstract}
    #### output a python dicionary and nothing else with the following keys
    reasoning: explain why the abstract directly addresses the problem statement, if it does not directly address the problem statement, explain why
    is_direct: True if the abstract directly addresses the problem statement, False if it does not
    is_relevant: from 1 to 5, how relevant is the abstract to the problem statement, 5 being the most relevant and directly addressing the problem statement, 1 meaning not relevant at all
    #### example output
    {{
        "reasoning": "<your reasoning>",
        "is_direct": True,
        "is_relevant": 5
    }}
    #### output dictionary ends here
    """
    return prompt

def create_google_reranking_prompt(problem_statement, search_results):
    search_results_str = "\n".join([f"{idx+1}: {result}" for idx, result in enumerate(search_results)])
    return f"""rerank the search results based on the problem statement and criteria below:
    #### problem statement:
    {problem_statement}
    #### criteria:
    - relevance to the problem statement
    - quality of the content
    - credibility of the source
    - recency of the content
    - any other criteria you think is important
    #### search results:
    {search_results_str}
    #### output:
    return only and only a python list of dictionaries, each dictionary should contain the following keys:
    {{
        "idx": int : index of the search result,
        "relevance": float : relevance score of the search result, from 0 to 10
        "quality": float : quality score of the search result, from 0 to 10
        "credibility": float : credibility score of the search result, from 0 to 10
        "recency": float : recency score of the search result, from 0 to 10
        "overall": float : overall score of the search result, from 0 to 100
    }}
    """

def create_google_reranking_prompt(problem_statement, search_results, top_k:int=10):
    search_results_str = "\n".join([f"{idx+1}: {result}" for idx, result in enumerate(search_results)])
    top_k_str = f"return top {max(1, min(top_k, len(search_results)))} search results"
    return f"""rerank the search results based on the problem statement and criteria below:
    #### problem statement:
    {problem_statement}
    #### criteria:
    - relevance to the problem statement
    - quality of the content
    - credibility of the source
    - recency of the content
    - any other criteria you think is important
    #### search results:
    {search_results_str}
    #### output:
    return only and only a python list of dictionaries, {top_k_str},
    each dictionary should contain the following keys:
    {{
        "idx": int : index of the search result,
        "relevance": float : relevance score of the search result, from 0 to 10
        "quality": float : quality score of the search result, from 0 to 10
        "credibility": float : credibility score of the search result, from 0 to 10
        "recency": float : recency score of the search result, from 0 to 10
        "overall": float : overall score of the search result, from 0 to 100
    }}
    """