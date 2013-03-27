# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
  try:
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
  except:
    return ''

setup(
  name = "firmata.py",
  version = "0.2.2",
  author = "Silas Snider",
  author_email = "swsnider@gmail.com",
  description = ("An API wrapper for the firmata wire protocol."),
  license = "APACHE",
  keywords = "firmata arduino serial",
  url = "https://github.com/swsnider/firmata.py",
  packages=['firmata', 'tests'],
  long_description=read('README.md'),
  classifiers=[
    "Development Status :: 3 - Alpha",
    "Topic :: Utilities",
    "License :: OSI Approved :: Apache Software License",
  ],
  install_requires=[
    "pyserial>=2.6",
    "unittest2"
  ]
)
