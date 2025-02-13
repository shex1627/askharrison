import streamlit as st
import pandas as pd
from typing import List, Dict
import datetime
from dataclasses import dataclass, asdict
import json
import os
from PIL import Image
import logging

# Importing required functions from the original script
from askharrison.SearchDatabase import SearchDatabase
from askharrison.prompts.query_expansion import generate_search_queries, generate_diffusion_search_queries
from askharrison.google_search import run_multiple_google_queries
from askharrison.prompts.content_curation import create_google_reranking_prompt
from askharrison.llm_models import process_question, safe_eval, extract_python_code

logger = logging.getLogger(__name__)

page_icon = Image.open("./icon.jpg")
# Streamlit App
st.set_page_config(page_title="Advanced Search App", 
    page_icon=page_icon,
    layout="centered",  # Change from "wide" to "centered"
    initial_sidebar_state="expanded"
)

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
        self.search_db = SearchDatabase()
        self.initialize_session_state()

    def initialize_session_state(self):
        if 'problem' not in st.session_state:
            st.session_state.problem = ""
        if 'query_type' not in st.session_state:
            st.session_state.query_type = "normal"
        if 'top_k' not in st.session_state:
            st.session_state['top_k'] = 10
        if 'num_queries' not in st.session_state:
            st.session_state.num_queries = 10
        if 'expanded_queries' not in st.session_state:
            st.session_state.expanded_queries = []
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'reranked_results' not in st.session_state:
            st.session_state.reranked_results = None

    def _save_search_results(self):
        search_data = {
            "problem": st.session_state.problem,
            "query_type": st.session_state.query_type,
            "num_queries": st.session_state.num_queries,
            "expanded_queries": st.session_state.expanded_queries,
            "search_results": [asdict(r) for r in st.session_state.search_results],
            "reranked_results": st.session_state.reranked_results.to_dict('records') if st.session_state.reranked_results is not None else None,
            "timestamp": datetime.datetime.now().isoformat()
        }
        return self.search_db.store_search(search_data)
    
    def _load_saved_search(self, search_id: str):
        """Load saved search into session state"""
        saved_search = self.search_db.get_search(search_id)
        if saved_search:
            st.session_state.problem = saved_search["problem"]
            st.session_state.query_type = saved_search["query_type"]
            st.session_state.num_queries = saved_search["num_queries"]
            st.session_state.expanded_queries = saved_search["expanded_queries"]
            st.session_state.search_results = [SearchResult(**r) for r in saved_search["search_results"]]
            if saved_search["reranked_results"]:
                st.session_state.reranked_results = pd.DataFrame(saved_search["reranked_results"])
            return True
        return False

    def run(self):
        # Handle UUID parameter first
        search_id = st.query_params.get("uuid")
        if search_id and self._load_saved_search(search_id):
            logger.info(f"Loaded saved search results for {search_id}")

        if os.environ.get('HIDE_MENU', 'true') == 'true':
                st.markdown("""
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    </style>
                    """, unsafe_allow_html=True)

        st.title("Advanced Search with Query Expansion and LLM Reranking")

        st.session_state.problem = st.text_input("Enter your search problem:", value=st.session_state.problem)
        st.session_state.query_type = st.radio("Select query expansion type:", 
                                               ("disable","normal", "diverse"), 
                                                index=querytype_to_index[st.session_state.query_type]
                                               )
        st.session_state.num_queries = st.slider("Number of queries to generate:", 5, 20, st.session_state.num_queries)
        st.session_state['top_k'] = st.slider("Number of results to rerank:", min_value=10, max_value=50, value=10)

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
                    st.session_state.problem, st.session_state.search_results, top_k=st.session_state.top_k
                )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    @staticmethod
    def _sanitize_filename(text: str, max_length: int = 30) -> str:
        """Convert query text to valid filename"""
        # Replace spaces and special chars with underscore
        sanitized = ''.join(c if c.isalnum() else '_' for c in text)
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        # Remove trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized

    def _get_base_filename(self) -> str:
        """Get base filename from first expanded query"""
        if not st.session_state.expanded_queries:
            return "search_results"
        first_query = st.session_state.expanded_queries[0]
        return self._sanitize_filename(first_query)
    
    def _display_results(self):
        base_filename = self._get_base_filename()

        st.subheader("LLM Reranked Results")
        df_display = st.session_state.reranked_results.copy()
        df_display['Relevance Score'] = df_display['overall'].apply(int)
        df_display = df_display[['title', 'link', 'snippet', 'Relevance Score']]

        # Add custom CSS for more compact cards
        st.markdown("""
            <style>
            .search-result-card {
                padding: 0.5rem 0;
                margin: 0.05rem 0;
            }
            .search-result-card h4 {
                margin: 0;
                font-size: 1rem;
                line-height: 1.2;
            }
            .search-result-card p {
                margin: 0.05rem 0;
                font-size: 0.9rem;
                line-height: 1.2;
            }
            .url-text {
                color: #666;
                font-size: 0.75rem;
                word-wrap: break-word;
                margin-top: 0.1rem !important;
            }
            hr {
                margin: 0.5rem 0 !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Display each result as a more compact card
        for _, row in df_display.iterrows():
            with st.container():
                st.markdown(f'<div class="search-result-card">', unsafe_allow_html=True)
                st.markdown(f"#### [{row['title']}]({row['link']})")
                st.markdown(f'<p><strong>Relevance Score:</strong> {row["Relevance Score"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p><strong>Summary:</strong> {row["snippet"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="url-text">{row["link"]}</p>', unsafe_allow_html=True)
                st.markdown("---")
                st.markdown('</div>', unsafe_allow_html=True)

        self._add_export_option(st.session_state.reranked_results, f"{base_filename}_reranked.csv")

        col1, col2 = st.columns(2)
        with col1:
            if  not st.query_params.get("uuid") and st.button("Share Search Results"):
                search_id = self._save_search_results()
                host_url = os.environ.get('HOST_URL', 'http://localhost:8501')
                url = f"{host_url}?uuid={search_id}"
                st.code(url, language=None)

        st.subheader("Expanded Search Queries")
        st.write(st.session_state.expanded_queries)
        self._add_export_option(st.session_state.expanded_queries, f"{base_filename}_queries.txt")

        st.subheader("All Search Results")
        self._display_search_results(st.session_state.search_results)

        self._add_export_all_button(base_filename)

    @staticmethod
    def _display_search_results(data: List[SearchResult]):
        # use one expander for all search results
        with st.expander("View all search results"):
            for i, result in enumerate(data):
                st.markdown(f"**Result {i+1}: {result.title}**")
                st.json(asdict(result))

    @staticmethod
    def _add_export_option(data, filename: str):
        if isinstance(data, pd.DataFrame):
            st.download_button(
                label=f"Download",
                data=data.to_csv(index=False).encode('utf-8'),
                file_name=filename,
                mime='text/csv',
            )
        elif isinstance(data, list):
            if filename.endswith('.txt'):
                st.download_button(
                    label=f"Download",
                    data='\n'.join(data),
                    file_name=filename,
                    mime='text/plain',
                )
            elif filename.endswith('.json'):
                st.download_button(
                    label=f"Download",
                    data=json.dumps(data, indent=2),
                    file_name=filename,
                    mime='application/json',
                )

    def _add_export_all_button(self, base_filename: str="search_results"):
        all_results = {
            "problem": st.session_state.problem,
            "query_type": st.session_state.query_type,
            "num_queries": st.session_state.num_queries,
            "expanded_queries": st.session_state.expanded_queries,
            "search_results": [asdict(r) for r in st.session_state.search_results],
            "reranked_results": st.session_state.reranked_results.to_dict('records') if st.session_state.reranked_results is not None else None
        }
        filename = f"{base_filename}_all_results.json"
        st.download_button(
            label="Export All Results",
            data=json.dumps(all_results, indent=2),
            file_name=filename,
            mime='application/json',
        )

if __name__ == "__main__":
    app = StreamlitApp()
    app.run()