from setuptools import setup, find_packages

setup(
    name="job_search_pipeline",
    version="1.0.0",
    description="Automated job search, extraction, and filtering pipeline",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "openai>=1.0.0",
        "playwright>=1.40.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.0",
        "tenacity>=8.2.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "rich>=13.0.0",
        "google-api-python-client>=2.100.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "job-search=main:main",
        ],
    },
)
