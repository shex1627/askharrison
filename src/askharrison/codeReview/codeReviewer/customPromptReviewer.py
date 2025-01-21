"""
This module defines a class CustomPromptReviewer that uses OpenAI's API to review code files.
It generates comprehensive prompts based on custom prompts and review scopes, and then
uses these prompts to review the code files provided.
"""

from typing import List, Optional, Dict
import openai
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomPromptReviewer:
    """
    A class that reviews code files using OpenAI's API by generating comprehensive prompts.
    """
    
    def __init__(self, api_key: str, custom_prompts: List[str], review_scopes: Optional[List[str]] = None, model: str = "text-davinci-003", max_tokens: int = 4000) -> None:
        """
        Initializes the CustomPromptReviewer with the necessary parameters.

        :param api_key: The API key for OpenAI.
        :param custom_prompts: A list of custom prompts to be included in the review.
        :param review_scopes: Optional list of scopes to focus the review on.
        :param model: The model to be used for generating prompts and reviews.
        :param max_tokens: The maximum number of tokens to be used in the API calls.
        """
        self.api_key = api_key
        self.custom_prompts = custom_prompts
        self.review_scopes = review_scopes or []
        self.model = model
        self.max_tokens = max_tokens
        openai.api_key = api_key
        self.client = openai.OpenAI()

    def review_code_files(self, file_paths: List[Path]) -> Dict[Path, Optional[str]]:
        """
        Reviews a list of code files and returns a dictionary with file paths as keys and review texts as values.

        :param file_paths: A list of file paths to the code files to be reviewed.
        :return: A dictionary mapping file paths to their respective review texts.
        """
        reviews = {}
        for file_path in file_paths:
            try:
                content = self.get_file_content(file_path)
                reviews[file_path] = self.review_code_file(file_path, content)
            except Exception as e:
                logger.error(f"Failed to review file {file_path}: {e}")
                reviews[file_path] = None
        return reviews

    def review_code_file(self, file_path: Path, content: str) -> Optional[str]:
        """
        Reviews a single code file.

        :param file_path: The path to the code file.
        :param content: The content of the code file.
        :return: The review text or None if an error occurred.
        """
        generated_prompt = self.generate_comprehensive_prompt()
        if generated_prompt:
            return self.review_code(content, generated_prompt)
        return None

    def generate_comprehensive_prompt(self) -> Optional[str]:
        """
        Generates a comprehensive prompt by combining custom prompts and review scopes.

        :return: A comprehensive prompt string or None if an error occurred.
        """
        try:
            combined_prompts = self.custom_prompts + [f"Review code for {scope}" for scope in self.review_scopes]
            prompt = "Combine the following prompts into a single comprehensive code review prompt:\n"
            prompt += "\n- " + "\n- ".join(combined_prompts)

            prompt_message = [
                {"role": "system", "content": "You are an experienced large language model prompt engineer."},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt_message,
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating comprehensive prompt: {e}")
            return None

    def review_code(self, code_chunk: str, generated_prompt: str) -> Optional[str]:
        """
        Reviews a chunk of code using a generated prompt.

        :param code_chunk: The code chunk to be reviewed.
        :param generated_prompt: The generated prompt to guide the review.
        :return: The review text or None if an error occurred.
        """
        try:
            prompt = f"""
            {generated_prompt}\n\n
            ###
            Code file content below, enclosed by triple back quotes: 
            ```
            {code_chunk}
            ```
            """
            prompt_message = [
                {"role": "system", "content": "You are an experienced software engineer and architect. You are reviewing code for a large software company. It is very important that you provide a thorough review of the code."},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt_message,
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error reviewing code: {e}")
            return None

    def get_file_content(self, file_path: Path) -> str:
        """
        Retrieves the content of a file.

        :param file_path: The path to the file.
        :return: The content of the file as a string.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

# Example usage:
if __name__ == "__main__":
    # Initialize the reviewer with the necessary parameters
    api_key = "your-api-key"
    custom_prompts = ["Check for PEP 8 compliance", "Optimize for performance"]
    file_paths = [Path("example.py")]

    reviewer = CustomPromptReviewer(api_key, custom_prompts)
    reviews = reviewer.review_code_files(file_paths)

    for file_path, review in reviews.items():
        if review:
            print(f"Review for {file_path}:\n{review}")
        else:
            print(f"Failed to review {file_path}.")