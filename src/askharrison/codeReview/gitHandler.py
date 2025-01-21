# git_handler.py

import subprocess

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
