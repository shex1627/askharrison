import streamlit as st
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass, asdict
import json

# Importing required functions from the original script
from askharrison.prompts.query_expansion import generate_search_queries, generate_diffusion_search_queries
from askharrison.google_search import run_multiple_google_queries
from askharrison.prompts.content_curation import create_google_reranking_prompt
from askharrison.llm_models import process_question, safe_eval, extract_python_code

@dataclass
class SearchResult:
    query: str
    title: str
    link: str
    snippet: str

querytype_to_index = {
    "disable": 0,
    "normal": 1,
    "diverse": 2
}

class SearchService:
    @staticmethod
    def expand_queries(problem: str, num_queries: int, query_type: str) -> List[str]:
        if query_type == "normal":
            return generate_search_queries(problem, num_queries, "google")
        elif query_type == "diverse":
            return generate_diffusion_search_queries(problem, num_queries, "google")
        elif query_type == "disable":
            return [problem]
        else:
            raise ValueError("Invalid query type")

    @staticmethod
    def perform_search(queries: List[str]) -> List[SearchResult]:
        query_results = run_multiple_google_queries(queries)
        processed_results = []
        for query, result in query_results.items():
            for item in result.get("items", []):
                processed_results.append(SearchResult(
                    query=query,
                    title=item["title"],
                    link=item["link"],
                    snippet=item["snippet"]
                ))
        return processed_results

    @staticmethod
    def rerank_results(problem: str, results: List[SearchResult], top_k: int) -> pd.DataFrame:
        results_dict = [asdict(r) for r in results]
        reranking_prompt = create_google_reranking_prompt(problem, results_dict, top_k=top_k)
        reranking_output = process_question(reranking_prompt, model="gpt-4o")
        python_code = extract_python_code(reranking_output)
        llm_output_objs = safe_eval(python_code)
        
        llm_output_df = pd.DataFrame(llm_output_objs)
        results_df = pd.DataFrame(results_dict)
        results_df_filtered = results_df[results_df.index.isin(llm_output_df['idx']-1)]
        
        final_df = pd.concat([results_df_filtered.reset_index(), llm_output_df], axis=1).sort_values("overall", ascending=False)
        return final_df.dropna()[['title', 'link', 'snippet', 'overall']]

class StreamlitApp:
    def __init__(self):
        self.search_service = SearchService()
        self.initialize_session_state()

    def initialize_session_state(self):
        if 'problem' not in st.session_state:
            st.session_state.problem = ""
        if 'query_type' not in st.session_state:
            st.session_state.query_type = "normal"
        if 'num_queries' not in st.session_state:
            st.session_state.num_queries = 10
        if 'expanded_queries' not in st.session_state:
            st.session_state.expanded_queries = []
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'reranked_results' not in st.session_state:
            st.session_state.reranked_results = None

    def run(self):
        st.set_page_config(page_title="Advanced Search App", layout="wide")
        st.title("Advanced Search with Query Expansion and LLM Reranking")

        st.session_state.problem = st.text_input("Enter your search problem:", value=st.session_state.problem)
        st.session_state.query_type = st.radio("Select query expansion type:", 
                                               ("disable","normal", "diverse"), 
                                                index=querytype_to_index[st.session_state.query_type]
                                               )
        st.session_state.num_queries = st.slider("Number of queries to generate:", 5, 20, st.session_state.num_queries)

        if st.button("Search"):
            if st.session_state.problem:
                self._perform_search()
            else:
                st.error("Please enter a search problem before proceeding.")

        if st.session_state.reranked_results is not None:
            self._display_results()

    def _perform_search(self):
        try:
            with st.spinner("Expanding queries..."):
                st.session_state.expanded_queries = self.search_service.expand_queries(
                    st.session_state.problem, st.session_state.num_queries, st.session_state.query_type
                )

            with st.spinner("Performing search..."):
                st.session_state.search_results = self.search_service.perform_search(st.session_state.expanded_queries)

            with st.spinner("Reranking results..."):
                st.session_state.reranked_results = self.search_service.rerank_results(
                    st.session_state.problem, st.session_state.search_results, top_k=10
                )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    def _display_results(self):
        st.subheader("Expanded Search Queries")
        st.write(st.session_state.expanded_queries)
        self._add_export_option(st.session_state.expanded_queries, "expanded_queries.txt")

        st.subheader("LLM Reranked Results")
        st.dataframe(st.session_state.reranked_results)
        self._add_export_option(st.session_state.reranked_results, "reranked_results.csv")

        st.subheader("All Search Results")
        self._display_search_results(st.session_state.search_results)

        self._add_export_all_button()

    @staticmethod
    def _display_search_results(data: List[SearchResult]):
        # use one expander for all search results
        with st.expander("View all search results"):
            for i, result in enumerate(data):
                st.markdown(f"**Result {i+1}: {result.title}**")
                st.json(asdict(result))
        # for i, result in enumerate(data):
        #     st.markdown(f"**Result {i+1}: {result.title}**")
        #     with st.expander("View details"):
        #         st.json(asdict(result))

    @staticmethod
    def _add_export_option(data, filename: str):
        if isinstance(data, pd.DataFrame):
            st.download_button(
                label=f"Download {filename}",
                data=data.to_csv(index=False).encode('utf-8'),
                file_name=filename,
                mime='text/csv',
            )
        elif isinstance(data, list):
            if filename.endswith('.txt'):
                st.download_button(
                    label=f"Download {filename}",
                    data='\n'.join(data),
                    file_name=filename,
                    mime='text/plain',
                )
            elif filename.endswith('.json'):
                st.download_button(
                    label=f"Download {filename}",
                    data=json.dumps(data, indent=2),
                    file_name=filename,
                    mime='application/json',
                )

    def _add_export_all_button(self):
        all_results = {
            "problem": st.session_state.problem,
            "query_type": st.session_state.query_type,
            "num_queries": st.session_state.num_queries,
            "expanded_queries": st.session_state.expanded_queries,
            "search_results": [asdict(r) for r in st.session_state.search_results],
            "reranked_results": st.session_state.reranked_results.to_dict('records') if st.session_state.reranked_results is not None else None
        }
        st.download_button(
            label="Export All Results",
            data=json.dumps(all_results, indent=2),
            file_name="all_search_results.json",
            mime='application/json',
        )

if __name__ == "__main__":
    app = StreamlitApp()
    app.run()