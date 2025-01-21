import streamlit as st
from askharrison.crawl.hrefCrawler import HrefCrawler
from askharrison.crawl.html_to_text import html_to_text
import json
import time
import logging 
import os

logger = logging.getLogger(__name__)


def crawl_data(base_url):
    try:
        # Instantiate the crawler
        crawler = HrefCrawler()
        
        # Perform the crawling
        results = crawler.crawl_from_url(base_url)
        
        url_to_html = {url: html_to_text(html.decode()) for url, html in results.items()}
        
        return url_to_html
    except Exception as e:
        st.error(f'An error occurred: {e}')
        return {}

st.title('Website Crawler App')
# hide menu
if os.environ.get('HIDE_MENU', 'true') == 'true':
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)

input_url = st.text_input('Enter the URL to crawl:', 'https://docs.trychroma.com/roadmap')

# Button to start crawling
if st.button('Crawl URL'):
    with st.spinner('Crawling...'):
        crawled_data = crawl_data(input_url)
    if crawled_data:
        st.write(f"Fetched {len(crawled_data)} pages.")
        json_to_download = json.dumps(crawled_data, indent=4)
        st.download_button(label='Download JSON',
                            data=json_to_download,
                            file_name='crawled_data.json',
                            mime='application/json')

        