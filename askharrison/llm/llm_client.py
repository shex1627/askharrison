from abc import ABC, abstractmethod

class LLMClient(ABC):
    def generate(self, prompt: str) -> str:
        """Generate text using LLM"""
        pass

