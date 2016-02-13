#!/usr/bin/env python

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages, Command
from setuptools.command.develop import develop
from setuptools.command.install import install

import subprocess
import os
import re

# create a decorator that wraps the normal develop and
# install commands to first update the version

def versioned(command_subclass):
    """
    A decorator for ensuring that installations, whether through setup.py install
    or setup.py develop, always update the version number with the Git revision and
    most recent tag.

    :param command_subclass:
    :return:
    """
    VERSION_PY = """
# This file is updated from Git information by running 'python setup.py
# version'.
__version__ = '%s'
"""
    orig_callable = command_subclass.run

    def modified_callable(self):
        if not os.path.isdir(".git"):
            print "This does not appear to be a Git repository."
            return
        try:
            p = subprocess.Popen(["git", "describe",
                                  "--tags", "--always"],
                                 stdout=subprocess.PIPE)
        except EnvironmentError:
            print "unable to run git, leaving idss-seration/_version.py alone"
            return
        stdout = p.communicate()[0]
        if p.returncode != 0:
            print "unable to run git, leaving idss-seriation/_version.py alone"
            return
        # our tags are like:  v2.2
        ver = stdout[len("v"):].strip()
        f = open("seriation/idss_version.py", "w")
        f.write(VERSION_PY % ver)
        f.close()
        print "updated _version.py to '%s'" % ver
        orig_callable(self)

    command_subclass.run = modified_callable
    return command_subclass


@versioned
class CustomDevelopClass(develop):
    pass

@versioned
class CustomInstallClass(install):
    pass

def get_version():
    try:
        f = open("seriation/idss_version.py")
    except EnvironmentError:
        return None
    for line in f.readlines():
        mo = re.match("__version__ = '([^']+)'", line)
        if mo:
            ver = mo.group(1)
            return ver
    return None


class VersionUpdate(Command):
    """setuptools Command"""
    description = "update version number"
    user_options = []


    def initialize_options(self):
        pass


    def finalize_options(self):
        pass


    def run(self):
        VERSION = """
# This file is updated from Git information by running 'python setup.py
# version'.
__version__ = '%s'
"""
        if not os.path.isdir(".git"):
            print "This does not appear to be a Git repository."
            return
        try:
            p = subprocess.Popen(["git", "describe",
                                  "--tags", "--always"],
                                 stdout=subprocess.PIPE)
        except EnvironmentError:
            print "unable to run git, leaving idss-seration/_version.py alone"
            return
        stdout = p.communicate()[0]
        if p.returncode != 0:
            print "unable to run git, leaving idss-seriation/_version.py alone"
            return
        # our tags are like:  v2.2
        ver = stdout[len("v"):].strip()
        f = open("seriation/idss_version.py", "w")
        f.write(VERSION % ver)
        f.close()
        print "updated _version.py to '%s'" % ver




setup(name="idss-seriation",
      #version=get_version(),
      version=get_version(),
      description="Iterative Deterministic Seriation Solution program for archaeological seriation",
      packages = find_packages(exclude=["test", "testdata", "utilities", "analysis", "doc", "featurelist"]),
      scripts = [
        'idss-seriation.py',
        'idss-seriation-mongodb.py',
	    'utilities/run-idss-batch.py',
        'utilities/idss-pickle-input.py',
        'utilities/idss-batch-builder.py'
      ],
      author='Carl P. Lipo and Mark E. Madsen',
      author_email='clipo@csulb.edu',
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
      license="APACHE",
      cmdclass={ "version": VersionUpdate, "install": CustomInstallClass, "develop": CustomDevelopClass },

      )