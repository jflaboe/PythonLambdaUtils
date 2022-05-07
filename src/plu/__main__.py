import sys
import plu.serve as serve
import plu.deploy as deploy

if len(sys.argv) > 1:
    if sys.argv[1] == "serve":
        serve.run()
    if sys.argv[1] == "deploy":
        deploy.run(sys.argv)