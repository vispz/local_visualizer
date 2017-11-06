#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('docs/source/HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['matplotlib']

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest',
]

setup(
    name='local_visualizer',
    version='0.2.0',
    description="Simple python api to visualize the plots in a script.",
    long_description=readme + '\n\n' + history,
    author="Vishnu P Sreenivasan",
    author_email='psvishnu.91@gmail.com',
    url='https://github.com/psvishnu91/local_visualizer',
    packages=find_packages(include=['local_visualizer']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='local_visualizer',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
