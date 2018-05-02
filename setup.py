# Copyright 2018 The Novo Nordisk Foundation Center for Biosustainability, DTU.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

from setuptools import setup, find_packages

import versioneer

setup_kwargs = {}

try:
    with open('README.md') as handle:
        readme = handle.read()
    setup_kwargs["long_description"] = readme
except IOError:
    setup_kwargs["long_description"] = ''

setup(
    name="cobrapy-bigg-client",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    install_requires=[
        "six",
        "cobra>=0.10.1",
        "requests",
        "pandas",
        "cachetools>=2.0"
    ],
    tests_require=[
        "pytest",
        "importlib_resources"
    ],
    package_data={
         '': [
             'test/data/*',
             'mlab/matlab_scripts/*m'
         ]
    },
    author="Joao Cardoso",
    author_email="joaca@biosustain.dtu.dk",
    description="BiGG API - programmatic access to the BiGG Models database",
    license="Apache License V2",
    keywords=("BiGG Models", "API"),
    url="https://opencobra.github.io/cobrapy_bigg_client",
    download_url='https://pypi.python.org/pypi/cobrapy_bigg_client',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    platforms="GNU/Linux, Mac OS X >= 10.7, Microsoft Windows >= 7",
    **setup_kwargs
)
