import requests
import pandas as pd
from typing import List, Dict, Any
from openai import OpenAI

from askharrison.config import API_KEY, SEARCH_ENGINE_ID, NUM_SEARCH_RESULTS

def google_custom_search(q):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": q,
        "num": NUM_SEARCH_RESULTS
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to search: {response.status_code}, {response.text}")