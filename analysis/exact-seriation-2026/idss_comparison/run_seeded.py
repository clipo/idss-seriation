# run the IDSS v2.0 command line unchanged after seeding the random number generators
import sys, random, runpy, numpy as np
sys.path.insert(0, "/home/claude/clipo/idss-v2.0")
random.seed(1); np.random.seed(1)
sys.argv = ["idss-seriation.py"] + sys.argv[1:]
runpy.run_path("/home/claude/clipo/idss-v2.0/idss-seriation.py", run_name="__main__")
