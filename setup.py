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
  version = "0.2.1",
  author = "Silas Snider",
  author_email = "swsnider@gmail.com",
  description = ("An API wrapper for the firmata wire protocol."),
  license = "MIT",
  keywords = "firmata arduino serial",
  url = "https://github.com/swsnider/firmata.py",
  packages=['firmata', 'tests'],
  long_description=read('README.md'),
  classifiers=[
    "Development Status :: 3 - Alpha",
    "Topic :: Utilities",
    "License :: OSI Approved :: MIT License",
  ],
  install_requires=[
    "pyserial>=2.6",
    "unittest2"
  ]
)
