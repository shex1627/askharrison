import json
import uuid
import os
import gzip
from typing import Dict, Any
from dataclasses import asdict

class SearchDatabase:
    def __init__(self, db_path: str = "search_results.json.gz"):
        self.db_path = db_path
        self.results: Dict[str, Any] = self._load_db()

    def _load_db(self) -> Dict[str, Any]:
        """Load the database from compressed JSON file"""
        if os.path.exists(self.db_path):
            with gzip.open(self.db_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_db(self):
        """Save the database to compressed JSON file"""
        with gzip.open(self.db_path, 'wt', encoding='utf-8') as f:
            json.dump(self.results, f)

    def store_search(self, search_data: Dict[str, Any]) -> str:
        """Store search results with UUID key"""
        search_id = str(uuid.uuid4())
        self.results[search_id] = search_data
        self._save_db()
        return search_id

    def get_search(self, search_id: str) -> Dict[str, Any]:
        """Retrieve search results by UUID"""
        return self.results.get(search_id)