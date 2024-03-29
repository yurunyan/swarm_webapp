from flask import Flask, request, render_template, redirect, session, escape, make_response, jsonify
from downloads import config
import requests, json, os, time
import tempfile
import pandas as pd
from uuid import uuid1, uuid4
from datetime import datetime
from pprint import pprint
import numpy as np

app = Flask(__name__, static_folder='static', static_url_path='/syaro/swarm/static/')
app.config['SECRET_KEY'] = os.urandom(8192)
app.config['JSON_AS_ASCII'] = False

@app.route('/syaro/swarm/', methods=['GET'])
def site_home():
    code = request.args.get('code', None)
    if config.debug:
        session['swarm'] = config.debug
    g = geojsonload()
    if not code and not session.get('swarm', None):
        print("authentication start", datetime.now())
        url = "https://foursquare.com/oauth2/authenticate?" + \
            f"client_id={config.app['key']}&response_type=code&redirect_uri={request.url_root}syaro/swarm"
        return redirect(url)
    if code and not session.get('swarm', None):
        url = "https://foursquare.com/oauth2/access_token?" + \
            f"client_id={config.app['key']}&client_secret={config.app['secret']}" + \
            f"&grant_type=authorization_code&redirect_uri={request.url_root}syaro/swarm&code={code}"
        x = json.loads(requests.get(url).text)
        if "access_token" in x.keys():
            session['swarm'] = x["access_token"]
        return redirect(config.app['redirect'])
    js = requests.get("https://api.foursquare.com/v2/venues/search", dict(
        oauth_token=session.get('swarm', None),
        m="swarm",
        v="20190930",
        radius=50 * 1000,
        ll="35.474834,139.367800"
    )).text
    for x in json.loads(js)['response']['venues']:
        loc = x['location']
        d = { "type": "Feature", "geometry": { "type": "Point", "coordinates": [ loc['lng'], loc['lat'] ] } }
        if not config.debug:
            g['features'].append(d)
    return render_template('swarm/index.html', app=config.app, g=json.dumps(g), v=uuid1())
    # js=json.dumps(js, indent=2, ensure_ascii=False)

def geojsonload():
    res = {
        "type": "FeatureCollection",
        "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
        "features": []
    }
    return res

@app.route('/syaro/swarm/search.json', methods=['GET'])
def api1():
    t = session.get('swarm', None) if not config.debug else config.debug
    ll = request.args.get('ll', None, str)
    categoryId = request.args.get('categoryId', None, str)
    if not t or not ll:
        return ''
    args = dict(oauth_token=t, m="swarm", v="20190930", radius=1000, ll=ll)
    if categoryId:
        args['categoryId'] = categoryId
    response = requests.get("https://api.foursquare.com/v2/venues/search", args)
    ratelimit = {
        'Remaining' : response.headers['X-RateLimit-Remaining'],
        'message' : "リクエスト残り(ユーザー) : " + response.headers['X-RateLimit-Remaining']
    }
    g = geojsonload()
    table = []
    for x in json.loads(response.text)['response']['venues']:
        loc = x['location']
        item = [
            x['name'], '\n'.join([xx['name'] for xx in x['categories']]), loc["distance"], 
            f'<button class="big ui button venue" id="venue" value="{x["id"]}">チェックインした友人数</button>' + \
                '<p class="friend"></p>', -1
        ]
        if "mayor" in x.keys():
            item[4] = x["mayor"]["count"]
        d = { "type": "Feature", "geometry": { "type": "Point", "coordinates": [ loc['lng'], loc['lat'] ] } }
        g['features'].append(d)
        table.append(item)
    pd.set_option("display.max_colwidth", 10000)
    df = pd.DataFrame(table)
    df.columns = ['name', 'category', 'distance', '', "mayor's check count"]
    # df["mayor's check count"].astype(np.int64)
    with tempfile.TemporaryDirectory() as x:
        df.to_html(f'{x}/x.html', index=False, escape=False)
        with open(f'{x}/x.html', 'r') as f:
            table = f.read()
    return make_response(jsonify(dict(geojson=g, table=table, ratelimit=ratelimit)), 200)

@app.route('/syaro/swarm/detail.json', methods=['GET'])
def api2():
    t = session.get('swarm', None) if not config.debug else config.debug
    i = request.args.get('id', '4d69fef30a25b60c64662c90', str)
    if not t:
        return make_response('', 400)
    args = dict(oauth_token=t, m="swarm", v="20190930")
    response = requests.get(f"https://api.foursquare.com/v2/venues/{i}", args)
    js = json.loads(response.text)
    js['ratelimit'] = {
        'Remaining' : response.headers['X-RateLimit-Remaining'],
        'message' : "リクエスト残り(ユーザー) : " + response.headers['X-RateLimit-Remaining']
    }
    js['friends_str'] = ''
    if "friendVisits" in js['response']['venue'].keys():
        for x in js['response']['venue']["friendVisits"]['items']:
            js['friends_str'] += x['user']['firstName']
            if "lastName" in x['user'].keys():
                js['friends_str'] += ' ' + x['user']['lastName']
            js['friends_str'] += ' ・ '
    js['friends_str'] += ' ...'
            
    return make_response(jsonify(js), 200)

if __name__ == "__main__":
    app.run(debug=True, threaded=True, processes=1)

