from setuptools import setup, find_packages

setup(
    name="common_utils",
    version="0.1.0",
    description="Common utilities for AWS Lambda apps",
    author="kevinL",
    packages=find_packages(),
    install_requires=[
        "openai==1.92.2",
        "boto3==1.38.25",
        "botocore==1.38.25",
        "pydantic",
        "pydantic-settings"
    ],
    python_requires='>=3.8'
)