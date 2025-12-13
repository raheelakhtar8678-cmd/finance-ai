from setuptools import setup, find_packages

setup(
    name="finance-ai",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pdfplumber',
        'pymupdf',
        'tabula-py',
        'pandas',
        'chromadb',
        'python-dotenv',
        'requests',
        'tiktoken',
    ],
)