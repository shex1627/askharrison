# Import all the possible reviewer classes
from askharrison.codeReview.codeReviewer.customPromptReviewer import CustomPromptReviewer


class CodeReviewerFactory:
    @staticmethod
    def get_reviewer_class(class_name):
        if class_name == 'CustomPromptReviewer':
            return CustomPromptReviewer
        # elif class_name == 'AnotherReviewer':
        #     return AnotherReviewer
        else:
            raise ValueError(f"Unknown reviewer class name: {class_name}")
