# Same as run_idss_fixed.py but with a threshold argument: run_thr.py in out.json boot seed threshold
import sys
sys.path.insert(0, "/home/claude/idsstest")
import run_idss_fixed as R
orig_init = R.DriverIDSS.initialize
THR = sys.argv.pop()
def init(self, args, argv):
    args["threshold"] = THR
    return orig_init(self, args, argv)
R.DriverIDSS.initialize = init
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3], "1", sys.argv[4]]
R.main()
