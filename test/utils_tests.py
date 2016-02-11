#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import logging as log
import unittest

from seriation.common_utilities import iso_filter_graphs, interassemblage_distance_euclidean

log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class UtilsTests(unittest.TestCase):


    def test_zero_distance(self):

        a = [0.5, 0.25, 0.25, 0.0]
        b = [0.5, 0.25, 0.25, 0.0]

        dist = interassemblage_distance_euclidean(a, b)

        self.assertEqual(0.0, dist)


    def test_nonzero_distance(self):
        a = [5,5]
        b = [10,10]
        ans = 7.07106781187

        pred = interassemblage_distance_euclidean(a,b)
        self.assertAlmostEqual(ans, pred, places=5)




if __name__ == "__main__":
    unittest.main()