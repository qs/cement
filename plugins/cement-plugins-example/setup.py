from setuptools import setup, find_packages
import sys, os

setup(name='CementExamplePlugin',
    version='0.1',
    description='Example Plugin for Applications Built on Cement',
    classifiers=[], 
    keywords='',
    author='BJ Dierkes',
    author_email='wdierkes@5dollarwhitebox.org',
    url='http://github.com/derks/cement',
    license='GNU GPLv3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "ConfigObj",
        "Cement",
        ],
    setup_requires=[
        "PasteScript >= 1.7"
        ],
    test_suite='nose.collector',
    entry_points="""
    """,
    namespace_packages=['cement', 'cement.plugins'],
    )
