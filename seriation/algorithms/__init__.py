#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Various implementations of seriation algorithms.

The algorithms are contained in this module to
allow easy development, optimization, and testing of the algorithms, independent of the scaffolding required
for production usage.

Production classes like IDSS contain the public API for performing a seriation, and hold references to implementations.
This allows analysis systems to be robust to change in the underlying algorithms, and potentially for multiple
algorithms to be used on the same data in parallel and the results compared.

"""