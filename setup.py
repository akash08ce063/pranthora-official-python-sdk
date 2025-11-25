from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="pranthora",
    version="1.0.0",
    description="The official Python SDK for the Pranthora Voice Assistant Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FirstPeak.AI",
    author_email="support@firstpeak.ai",
    url="https://github.com/FirstPeakAI/pranthora-python",
    packages=find_packages(),
    install_requires=[
        "requests>=2.20.0",
        "websockets>=10.0",
    ],
    extras_require={
        "realtime": [
            "pyaudio>=0.2.11",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    keywords="voice assistant, ai, pranthora, firstpeak, sdk",
    project_urls={
        "Documentation": "https://docs.firstpeak.ai",
        "Source": "https://github.com/FirstPeakAI/pranthora-python",
        "Tracker": "https://github.com/FirstPeakAI/pranthora-python/issues",
    },
)
