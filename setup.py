from setuptools import setup, find_packages

setup(
    name="text_to_sql",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "sqlalchemy>=2.0.0",
        "openai>=1.0.0",
        "langchain>=0.0.300",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "tabulate>=0.9.0",
        "rich>=13.0.0",
        "psycopg2-binary>=2.9.5",
        "anthropic>=0.18.0",
        "google-generativeai>=0.3.0",
        "requests>=2.31.0",
        "scikit-learn>=1.2.0",
        "numpy>=1.21.0",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "joblib>=1.2.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "text2sql=app.cli:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="一個將自然語言轉換為 SQL 查詢的工具",
    keywords="text-to-sql, nlp, ai, postgresql",
    python_requires=">=3.8",
)