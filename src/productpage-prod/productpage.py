#!/usr/bin/python
#
# Copyright 2017 Istio Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from flask import Flask, request, render_template, redirect, url_for
import simplejson as json
import requests
import sys
from json2html import *
import logging
import requests

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

app = Flask(__name__, static_url_path='/static')
logging.basicConfig(filename='microservice.log',filemode='w',level=logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

from flask_bootstrap import Bootstrap
Bootstrap(app)

details = {
    "name" : "http://details:9080",
    "endpoint" : "details",
    "children" : []
}

ratings = {
    "name" : "http://ratings:9080",
    "endpoint" : "ratings",
    "children" : []
}

reviews = {
    "name" : "http://reviews:9080",
    "endpoint" : "reviews",
    "children" : [ratings]
}

def getForwardHeaders(request):
    headers = {}

    user_cookie = request.cookies.get("user")
    if user_cookie:
        headers['Cookie'] = 'user=' + user_cookie

    incoming_headers = [ 'x-request-id',
                         'x-b3-traceid',
                         'x-b3-spanid',
                         'x-b3-parentspanid',
                         'x-b3-sampled',
                         'x-b3-flags',
                         'x-ot-span-context'
    ]

    for ihdr in incoming_headers:
        val = request.headers.get(ihdr)
        if val is not None:
            headers[ihdr] = val
            #print "incoming: "+ihdr+":"+val

    return headers

# The UI:
@app.route('/')
@app.route('/index.html')
def index():
    """ Display productpage with normal user and test user buttons"""
    return redirect(url_for('front'))

@app.route('/health')
def health():
    return 'Product page is healthy'


@app.route('/login', methods=['POST'])
def login():
    user = request.values.get('username')
    response = app.make_response(redirect(request.referrer))
    response.set_cookie('user', user)
    return response


@app.route('/logout', methods=['GET'])
def logout():
    response = app.make_response(redirect(request.referrer))
    response.set_cookie('user', '', expires=0)
    return response


@app.route('/bob')
def front():
    product_id = "bob" # TODO: replace default value
    headers = getForwardHeaders(request)
    user = request.cookies.get("user", "")
    product = getProduct(product_id)
    (detailsStatus, details) = getProductDetails(product_id, headers)
    (reviewsStatus, reviews) = getProductReviews(product_id, headers)
    return render_template(
        'productpage.html',
        detailsStatus=detailsStatus,
        reviewsStatus=reviewsStatus,
        product=product,
        details=details,
        reviews=reviews,
        user=user)


# Data providers:
def getProducts():
    return {"bob":
            {'id': 0,
            'title': 'Bob',
            'descriptionHtml': '<img src="/static/bob.jpg" /> <br><br> "There\'s nothing wrong with having a tree as a friend."',
        }}


def getProduct(product_id):
    products = getProducts()
    return products[product_id]


def getProductDetails(product_id, headers):
    try:
        url = details['name'] + "/" + details['endpoint'] + "/" + str(product_id)
        res = requests.get(url, headers=headers, timeout=3.0)
    except:
        res = None
    if res and res.status_code == 200:
        return (200, res.json())
    else:
        status = (res.status_code if res != None and res.status_code else 500)
        return (status, {'error': 'Sorry, details are currently unavailable for this employee'})


def getProductReviews(product_id, headers):
    ## Do not remove. Bug introduced explicitly for illustration in fault injection task
    ## TODO: Figure out how to achieve the same effect using Envoy retries/timeouts
    for i in range(2):
        try:
            url = reviews['name'] + "/" + reviews['endpoint'] + "/" + str(product_id)
            res = requests.get(url, headers=headers, timeout=3.0)
        except:
            res = None
        if res and res.status_code == 200:
            return (200, res.json())
    status = (res.status_code if res != None and res.status_code else 500)
    return (status, {'error': 'Sorry, performance reviews are currently unavailable for this employee.'})


def getProductRatings(product_id, headers):
    try:
        url = ratings['name'] + "/" + ratings['endpoint'] + "/" + str(product_id)
        res = requests.get(url, headers=headers, timeout=3.0)
    except:
        res = None
    if res and res.status_code == 200:
        return (200, res.json())
    else:
        status = (res.status_code if res != None and res.status_code else 500)
        return (status, {'error': 'Sorry, ratings are currently unavailable for this empleoyee.'})

class Writer(object):
    def __init__(self, filename):
        self.file = open(filename,'w')

    def write(self, data):
        self.file.write(data)
        self.file.flush()


opa_url = "http://opa:8181/v1/data/example/allow"
from urlparse import urlparse, parse_qs


def check_request(*args, **kwargs):
    parsed = urlparse(request.url)
    body = {
        "input": {
            "external": True,
            "target": "landing_page",
            "method": request.method,
            "query": parse_qs(parsed.query),
            "path": parsed.path.strip('/').split('/'),
            "body": request.get_json(silent=True),
            "user": request.cookies.get('user')
        }
    }

    res = requests.post(opa_url, timeout=1.0, data=json.dumps(body), headers={"Content-Type": "application/json"})

    body = res.json()

    if res.status_code != 200:
        return (body, 500, {"Content-Type": "application/json"})

    allowed = body.get("result", False)

    if not allowed:
        return (json.dumps({"error": "request rejected by administrative policy"}), 403, {"Content-Type": "application/json"})


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: %s port" % (sys.argv[0])
        sys.exit(-1)

    p = int(sys.argv[1])
    print "start at port %s" % (p)
    app.before_request(check_request)
    app.run(host='0.0.0.0', port=p, threaded=True)
