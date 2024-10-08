from collections import defaultdict
import arxiv
from tqdm import tqdm
from askharrison.llm_models import process_question, safe_eval, extract_python_code
from askharrison.prompts.query_expansion import generate_search_queries_prompt
from askharrison.config import ARXIV_NUM_EXPANEDED_QUERIES, ARXIV_NUM_SEARCH_RESULTS

def expand_arxiv_query(problem_statement: str, model="gpt-4") -> list[str]:
    """
    Expand a query using LLM and return a list of queries
    """
    prompt = generate_search_queries_prompt(problem_statement, ARXIV_NUM_EXPANEDED_QUERIES, "arxiv")
    queries_llm_output = process_question(prompt, model=model)
    queries = safe_eval(extract_python_code(queries_llm_output))
    return queries

def run_multi_arixv_queries(queries: list[str]):
    """
    Run multiple queries on arxiv and return the results
    """
    query_to_results = defaultdict(list)
    for query in tqdm(queries):
        search_results = arxiv.Search(
            query=query,
            max_results=ARXIV_NUM_SEARCH_RESULTS,
            sort_by=arxiv.SortCriterion.Relevance,
            #start=start_index
        )
        for result in search_results.results():
        # convert result into a dictionary, find all the attributes then add them to the dictionary
            result_dict = {}
            #print(result.title)
            result_attributes = [attribute for attribute in dir(result) if not attribute.startswith("_") and not callable(getattr(result, attribute))]
            for attribute in result_attributes:
                result_dict[attribute] = getattr(result, attribute)
            # add the query to the dictionary
            query_to_results[query].append(result_dict)
    return query_to_results