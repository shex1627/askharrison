# code_reviewer.py

class CodeReviewer:
    def review_code_files(self, file_paths):
        raise NotImplementedError("This method should be implemented by subclasses")

    def review_code_file(self, file_path, content):
        raise NotImplementedError("This method should be implemented by subclasses")
