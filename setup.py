
import os, subprocess, re
from distutils.core import setup, Command
from distutils.command.sdist import sdist as _sdist

# class Test(Command):
#     description = "run unit tests"
#     user_options = []
#     boolean_options = []
#     def initialize_options(self):
#         pass
#     def finalize_options(self):
#         pass
#     def run(self):
#         pass
#         # EXAMPLE - needs customization here
#         # from ecdsa import numbertheory
#         # numbertheory.__main__()
#         # from ecdsa import ellipticcurve
#         # ellipticcurve.__main__()
#         # from ecdsa import ecdsa
#         # ecdsa.__main__()
#         # from ecdsa import test_pyecdsa
#         # test_pyecdsa.unittest.main(module=test_pyecdsa, argv=["dummy"])
#         # all tests os.exit(1) upon failure

VERSION_PY = """
# This file is updated from Git information by running 'python setup.py
# version'.
__version__ = '%s'
"""

def update_version_py():
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
    print "set _version.py to '%s'" % ver

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

class Version(Command):
    description = "update _version.py from Git repo"
    user_options = []
    boolean_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        update_version_py()
        print "Version is now", get_version()

class sdist(_sdist):
    def run(self):
        update_version_py()
        # unless we update this, the sdist command will keep using the old
        # version
        self.distribution.metadata.version = get_version()
        return _sdist.run(self)



setup(name="idss-seriation",
      version=get_version(),
      description="Iterative Deterministic Seriation Solution program for archaeological seriation",
      packages = [
        'seriation',
      ],
      scripts = [
          'idss-seriation.py',
          'idss-seriation-mongodb.py',
	  'utilities/run-idss-batch.py'
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
      cmdclass={ "version": Version, "sdist": sdist },
      )
