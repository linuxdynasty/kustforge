# setup.py
from setuptools import setup, find_packages

setup(
    name="kustomize_wrapper",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "boto3>=1.26.0",
        "pyyaml>=5.1",
        "colorama>=0.4.4",
        "kubernetes>=12.0.0",
        "cryptography>=3.4.7"
    ],
    entry_points={
        "console_scripts": [
            "kustomize-wrapper=main:main",
        ],
    },
    python_requires=">=3.7",
    author="Your Name",
    description="Kustomize wrapper with AWS resource resolution and template processing",
)
