# coding: utf-8

"""
    mmopdca API

    Command-DSL-driven forecasting micro-service API only

    The version of the OpenAPI document: 0.4.0
    Contact: gtocue510@gmail.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from setuptools import setup, find_packages  # noqa: H301

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools
NAME = "mmopdca-sdk"
VERSION = "1.0.0"
PYTHON_REQUIRES = ">= 3.9"
REQUIRES = [
    "urllib3 >= 2.1.0, < 3.0.0",
    "python-dateutil >= 2.8.2",
    "pydantic >= 2",
    "typing-extensions >= 4.7.1",
]

setup(
    name=NAME,
    version=VERSION,
    description="mmopdca API",
    author="gtocue",
    author_email="gtocue510@gmail.com",
    url="",
    keywords=["OpenAPI", "OpenAPI-Generator", "mmopdca API"],
    install_requires=REQUIRES,
    packages=find_packages(exclude=["test", "tests"]),
    include_package_data=True,
    long_description_content_type='text/markdown',
    long_description="""\
    Command-DSL-driven forecasting micro-service API only
    """,  # noqa: E501
    package_data={"mmopdca_sdk": ["py.typed"]},
)