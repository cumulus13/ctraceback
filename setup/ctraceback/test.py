import sys
from custom_traceback import CTraceback

try:
    print(sys.argv[1])
except:
    CTraceback(*sys.exc_info())