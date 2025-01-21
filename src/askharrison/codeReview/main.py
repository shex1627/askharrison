# main.py
import os 
from askharrison import codeReview
from askharrison.codeReview.codeReviewerconfig_manager import ConfigManager
from askharrison.codeReview.utils import detect_language, GitHandler
from askharrison.codeReview.reviewLogger import Logger
from askharrison.codeReview.codeReviewer.customPromptReviewer import CustomPromptReviewer

def main():
    CONFIG_PATH = os.environ.get("CONFIG_PATH", os.path.join(os.path.dirname(codeReview.__file__), "reviewconfig.yaml"))
    config_manager = ConfigManager(CONFIG_PATH)
    git_handler = GitHandler()
    logger = Logger(__name__)
    reviewer = OpenAIReviewer(config_manager.get("openai_api_key"))

    staged_files = git_handler.get_staged_files()
    generated_prompt = reviewer.generate_comprehensive_prompt(
        config_manager.get("review_scopes"),
        config_manager.get("custom_prompts")
    )

    if not generated_prompt:
        logger.error("Could not generate a comprehensive prompt for review.")
        return

    for file_path in staged_files:
        language = detect_language(file_path)
        logger.info(f"Reviewing {file_path} for language: {language}")
        content = git_handler.get_file_changes(file_path, config_manager.get("review_changes_only", True))
        review_result = reviewer.review_code(content, generated_prompt)
        if review_result:
            logger.info(f"Review for {file_path}: {review_result}")
        else:
            logger.error(f"Failed to review {file_path}")

if __name__ == "__main__":
    main()
