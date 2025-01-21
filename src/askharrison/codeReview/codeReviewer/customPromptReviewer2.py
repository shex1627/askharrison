# custom_prompt_reviewer.py

import openai
from openai import OpenAI
from askharrison.codeReview.codeReviewer.codeReviewer import CodeReviewer
from askharrison.codeReview.reviewLogger import Logger

logger = Logger(__name__)

class CustomPromptReviewer(CodeReviewer):    
    def __init__(self, api_key, custom_prompts, review_scopes=None, model="text-davinci-003", max_tokens=4000):
        self.api_key = api_key
        self.custom_prompts = custom_prompts
        self.review_scopes = review_scopes if review_scopes else []
        self.model = model
        self.max_tokens = max_tokens
        openai.api_key = api_key
        self.client = OpenAI()

    def review_code_files(self, file_paths):
        reviews = {}
        for file_path in file_paths:
            content = self.get_file_content(file_path)  # This method needs to be defined
            reviews[file_path] = self.review_code_file(file_path, content)
        return reviews

    def review_code_file(self, file_path, content):
        generated_prompt = self.generate_comprehensive_prompt()
        return self.review_code(content, generated_prompt)

    def generate_comprehensive_prompt(self):
        # Use the LLM model to combine all custom prompts and review scopes into a single prompt
        try:
            # We include the review scopes as part of the custom prompts
            combined_prompts = self.custom_prompts + [f"Review code for {scope}" for scope in self.review_scopes]
            prompt = "Combine the following prompts into a single comprehensive code review prompt:"
            prompt += "\n- " + "\n- ".join(combined_prompts)

            prompt_message = [
                {"role": "system", "content": "You are an experiend large language model prompt engineer."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model = self.model,
                messages=prompt_message,
                temperature=0.0,
            )
            # The assumption here is that the model will return a single, well-formed prompt.
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            print(f"Error generating comprehensive prompt: {e}")
            logger.error(f"Error generating comprehensive prompt: {e}")
            return None

    def review_code(self, code_chunk, generated_prompt):
        try:
            prompt=f""""
            {generated_prompt}\n\n
            ###
            Code file content below, enclosed by triple back quotes: 
            ```
            {code_chunk}
            ```
            """
            prompt_message = [
                {"role": "system", "content": "You are an extinguished software engineer and architect. You are reviewing code for a large software company. It is very important that you provide a thorough review of the code."},
                {"role": "user", "content": prompt}
            ]
            print(prompt)
            response = self.client.chat.completions.create(
                model = self.model,
                messages=prompt_message,
                temperature=0.0,
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            logger.error(f"Error reviewing code: {e}")
            return None

    # Placeholder for the method to get file content
    def get_file_content(self, file_path):
        # This method should retrieve the file's content.
        # For now, we'll just read the content from the file directly.
        with open(file_path, 'r') as file:
            return file.read()
