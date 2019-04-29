# pylint: disable=missing-docstring
from setuptools import setup, find_packages

with open('README.md') as f:
    README = f.read()

setup(
    name='logsense-opentracing-tracker',
    version='0.1.3',
    description='Logsen Opentracing Tracker',
    long_description=README,
    author='Dominik Rosiek',
    author_email='drosiek@collective-sense.com',
    url='https://github.com/collectivesense/logsense-opentracing-python',
    license=None,
    packages=find_packages(exclude=('examples',)),
    install_requires=[
        'opentracing==2.0.0',
        'logsense-logger==0.2.0'
        ]
)
