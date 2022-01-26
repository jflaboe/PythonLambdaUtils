import sys
import plu.serve as serve

if len(sys.argv) > 1:
    if sys.argv[1] == "serve":
        serve.run()