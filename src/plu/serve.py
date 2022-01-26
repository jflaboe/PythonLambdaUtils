from flask import Flask, request
from os.path import exists
import importlib.util
import json

app = Flask(__name__)

route = ""
config = {}
if exists(".plu"):
    with open(".plu") as f:
        config =json.loads(f.read())

route_reactions = {}

for r, d in config.items():
    if exists(d):
        spec = importlib.util.spec_from_file_location("lambda_function", d + "/lambda_function.py")
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        route_reactions[r] = plugin

if "route" in config:
    route = config["route"]

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def lamdba_response(path):
    body = ""
    if request.method == "POST":
        body = json.dumps(request.get_json(force=True))
    event = {
        'version': '2.0',
        'routeKey': 'ANY ' + request.path,
        'rawPath': request.path,
        'rawQueryString': '',
        'headers': {
            'accept': '*/*',
            'accept-encoding':
            'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'content-length': '271',
            'content-type': 'text/plain;charset=UTF-8',
            'sec-ch-ua': '" Not;A Brand";v="99","Google Chrome";v="97", "Chromium";v="97"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
            'x-amzn-trace-id': 'Root=1-61e67efc-540dc3397c5c306c1a5a2147',
            'x-forwarded-for': '68.174.127.45',
            'x-forwarded-port': '443',
            'x-forwarded-proto': 'https'
        },
        'requestContext': {
            'domainPrefix': 'api',
            'http': {
                'method': 'POST',
                'path': request.path,
                'protocol': 'HTTP/1.1',
                'sourceIp': '68.174.127.45',
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
            },
            'routeKey': request.path,
            'stage': '$default',
            'time': '18/Jan/2022:08:49:00 +0000',
            'timeEpoch': 1642495740013
        },
        'body': body,
        'isBase64Encoded': False
    }

    resp = ""
    if request.path in route_reactions:
        print(route_reactions)
        print(dir(route_reactions[request.path]))
        resp = route_reactions[request.path].lambda_handler(event, None)
    return resp


def run():
    app.run(host="localhost", port=3030, debug=True)