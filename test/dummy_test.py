#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import logging as log
import unittest


log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class DummyTest(unittest.TestCase):


    def test_get_travis_working(self):
        self.assertTrue(True)





if __name__ == "__main__":
    unittest.main()