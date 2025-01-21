import subprocess
import os

def detect_language(file_path):
    """
    Detect the programming language of a file based on its extension.
    """
    extension_to_language = {
        ".py": "Python",
        ".js": "JavaScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cs": "C#",
        ".rb": "Ruby",
        ".go": "Go",
        ".php": "PHP",
        ".ts": "TypeScript",
        # Add more mappings as needed
    }
    extension = os.path.splitext(file_path)[1]
    return extension_to_language.get(extension, "Unknown")


class GitHandler:
    @staticmethod
    def get_staged_files():
        return subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True).splitlines()

    @staticmethod
    def get_file_changes(file_path, review_changes_only):
        if review_changes_only:
            return subprocess.check_output(['git', 'diff', '--cached', file_path], text=True)
        else:
            with open(file_path, 'r') as file:
                return file.read()
