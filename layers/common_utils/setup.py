from setuptools import setup, find_packages
import os

def parse_requirements(filename):
    req_path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.isfile(req_path):
        return []
    with open(req_path) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return lines

print(parse_requirements("requirements.txt"))

setup(
    name="common_utils",
    version="0.1.0",
    description="Common utilities for AWS Lambda apps",
    author="kevinL",
    packages=find_packages(),
    install_requires=parse_requirements("requirements.txt"),
    python_requires='>=3.8'
)