#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

description = """
PostgreSQL json field support for Django.
"""


setup(
    name="azv-django-pgjson",
    version="0.0.0",
    url="https://github.com/moradology/azv-django-pgjson",
    license="BSD",
    platforms=["OS Independent"],
    description=description.strip(),
    author="",
    author_email="",
    keywords="django, postgresql, pgsql, json, field",
    maintainer="",
    maintainer_email="",
    packages=find_packages(),
    include_package_data=False,
    install_requires=[
        "Django >=1.8",
        "psycopg2 >=2.6"
    ],
    zip_safe=False,
    test_suite='tests',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Topic :: Internet :: WWW/HTTP",
    ]
)
