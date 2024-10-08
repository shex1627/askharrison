import json
import os

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the resources directory
resources_dir = os.path.join(os.path.dirname(current_dir), 'resources')

# Load credentials and access codes
with open(os.path.join(resources_dir, "info.json")) as f:
    CREDS = json.load(f)

with open(os.path.join(resources_dir, "access_codes.txt")) as f:
    VALID_ACCESS_CODES = [line.strip() for line in f]

# API configurations
API_KEY = CREDS["api_key"]
SEARCH_ENGINE_ID = CREDS["internet_cx"]

# Model configurations
DEFAULT_MODEL = "gpt-4"

# File paths
USER_DATA_DIR = os.path.join(os.path.dirname(current_dir), "user_data")

# Search configurations
NUM_SEARCH_QUERIES = 10
NUM_SEARCH_RESULTS = 10

ARXIV_NUM_SEARCH_RESULTS = 20
ARXIV_NUM_EXPANEDED_QUERIES = 10