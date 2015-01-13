from distutils.core import setup

setup(name="idss-seriation",
      version="2.0",
      packages = [
        'seriation',
      ],
      scripts = [
          'bin/idss-seriation.py',
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
      ]
      )
