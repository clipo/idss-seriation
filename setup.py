#!/usr/bin/env python

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages, Command
from setuptools.command.develop import develop
from setuptools.command.install import install

import subprocess
import os
import re




setup(name="idss-seriation",
      #version=get_version(),
      version="2.5.1",
      description="Iterative Deterministic Seriation Solution program for archaeological seriation",
      packages = find_packages(exclude=["test", "testdata", "utilities", "analysis", "doc", "featurelist"]),
      scripts = [
        'idss-seriation.py',
        'idss-seriation-mongodb.py',
	    'utilities/run-idss-batch.py',
        'utilities/idss-pickle-input.py',
        'utilities/idss-batch-builder.py',
	'utilities/frequencySeriationMaker.py',
	'utilities/occurrenceSeriationMaker.py'
      ],
      author='Carl P. Lipo and Mark E. Madsen',
      author_email='clipo@binghamton.edu',
      url='https://github.com/clipo/idss-seriation',
      classifiers=[
          'Development Status :: 2 - Beta',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2.7',
          'Topic :: Scientific/Engineering',
      ],
      license="APACHE"
      )
