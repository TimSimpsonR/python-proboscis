# vim: tabstop=4 shiftwidth=4 softtabstop=4


# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="proboscis",
    version="1.2.6.0",
    author='Rackspace',
    author_email='tim.simpson@rackspace.com',
    description="Extends Nose with certain TestNG like features.",
    keywords="nose test testng",
    long_description="Proboscis is a Python test framework that extends "
                    "Python's built-in unittest module and Nose with "
                    "features from TestNG.",
    url='https://github.com/rackspace/python-proboscis',
    license='Apache',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    py_modules=[],
    packages=['proboscis', 'proboscis.compatability'],
    scripts=[],
    tests_require=["nose"],
    test_suite="nose.collector"
)
