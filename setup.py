from setuptools import setup, find_packages
# install requirements from requirements.txt
# add github link to setup.py
setup(
    name="askharrison",
    version="0.1.2c",
    packages=find_packages(),
    description="A package for the AskHarrison, including various GenAI tools",
    long_description="A package for the AskHarrison, including various GenAI tools",
    url="https://github.com/shex1627/askharrison",
    project_urls={                                    # Additional links
        "Source Code": "https://github.com/shex1627/askharrison",
    },
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