# pylint: disable=missing-docstring
from setuptools import setup, find_packages
from os import chdir
from os.path import dirname, realpath, join


package_dir = dirname(realpath(__file__))

with open(join(package_dir, 'logsense_opentracing', 'version.py')) as f:
    exec(f.read())

with open(join(package_dir, 'README.md')) as f:
    README = f.read()

with open(join(package_dir, 'LICENSE.md')) as f:
    LICENSE = f.read()

setup(
    name='logsense-opentracing-tracker',
    version=__version__,
    description='Logsense Opentracing Tracker',
    long_description=README,
    author='Dominik Rosiek',
    author_email='drosiek@collective-sense.com',
    url='https://github.com/collectivesense/logsense-opentracing-python',
    license=LICENSE,
    packages=find_packages(exclude=('examples', 'tests')),
    install_requires=[
        'opentracing==2.0.0',
        'logsense-logger==0.2.0'
        ],
    extras_require={
        'flask': [
            'flask'
        ]
    }
)
