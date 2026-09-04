import os
import sys

# These test-support modules are edited constantly while skills and adapters are
# written. Python decides a cached .pyc is fresh by source mtime and size, at
# one-second granularity, so a same-second edit that keeps the size can be missed
# and a stale module imported. That produced two false test failures during
# development, which is worse than a slow suite: a mutation battery that can lie
# to you is the thing you trust when you stop looking.
sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
