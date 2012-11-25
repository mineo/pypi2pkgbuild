#!/usr/bin/env python
from distutils.core import setup
setup(name="pypi2pkgbuild",
      version=1,
      author="Wieland Hoffmann",
      author_email="themineo@gmail.com",
      license="MIT",
      scripts=["pypi2pkgbuild.py"],
      classifiers=["Development Status :: 4 - Beta",
          "License :: OSI Approved :: MIT License",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3.3"],
)
