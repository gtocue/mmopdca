from pathlib import Path
from setuptools import setup, find_packages

README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

setup(
    name                = "mmopdca-sdk",
    version             = "1.0.0",
    description         = "mmopdca API Python SDK",
    long_description    = README,
    long_description_content_type = "text/markdown",
    author              = "gtocue",
    author_email        = "gtocue510@gmail.com",
    url                 = "https://github.com/gtocue/mmopdca",
    python_requires     = ">=3.9",
    install_requires = [
        "urllib3>=2.1.0,<3.0.0",
        "python-dateutil>=2.8.2",
        "pydantic>=2",
        "typing-extensions>=4.7.1",
    ],
    extras_require = {
        "dev": [
            "fastapi>=0.111,<0.117",
            "uvicorn[standard]>=0.29,<0.32",
            "pytest>=8",
            "pyyaml>=6",
            "black>=25",
        ]
    },
    packages             = find_packages(exclude=("test", "tests")),
    include_package_data = True,
    package_data         = {"mmopdca_sdk": ["py.typed"]},
    license              = "MIT",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
