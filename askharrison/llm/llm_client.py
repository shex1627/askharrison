from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    async def async_generate(self, prompt: str) -> str:
        """Generate text using LLM"""
        pass

    def generate(self, prompt: str) -> str:
        """Generate text using LLM"""
        pass

