from setuptools import setup, find_packages
# install requirements from requirements.txt
setup(
    name="askharrison",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "requests",
        "pyarxiv",
        "transformers",
        "ipykernel",
        "pandas",
        "numpy",
        "arxiv",
        "openai==1.29.0",
        "tiktoken",
        "Pillow",            
        ]
)