from setuptools import setup, find_packages

setup(
    name="job_posting_analyzer",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        # Add your package dependencies here
    ],
    author="Sean La",
    author_email="sean.la.msc@icloud.com",
    description="Analyze job posts with LLMs",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/sean-la/job-posting-analyzer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)