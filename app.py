from flask import Flask, request, render_template, redirect, session, escape, make_response, jsonify
from downloads import config
import requests, json, os, time
import tempfile
import pandas as pd

app = Flask(__name__, static_folder='static', static_url_path='/syaro/swarm/static/')
app.config['SECRET_KEY'] = os.urandom(8192)

@app.route('/syaro/swarm/', methods=['GET'])
def site_home():
    code = request.args.get('code', None)
    if config.debug:
        session['swarm'] = config.debug
    g = geojsonload()
    if not code and not session.get('swarm', None):
        time.sleep(3)
        url = "https://foursquare.com/oauth2/authenticate?" + \
            f"client_id={config.app['key']}&response_type=code&redirect_uri={config.app['redirect']}"
        return redirect(url)
    if code and not session.get('swarm', None):
        url = "https://foursquare.com/oauth2/access_token?" + \
            f"client_id={config.app['key']}&client_secret={config.app['secret']}" + \
            f"&grant_type=authorization_code&redirect_uri={config.app['redirect']}&code={code}"
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
        g['features'].append(d)
    return render_template('swarm/index.html', app=config.app, g=json.dumps(g), v=os.urandom(16))
    # js=json.dumps(js, indent=2, ensure_ascii=False)

def geojsonload():
    res = {
        "type": "FeatureCollection",
        "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
        "features": []
    }
    return res

@app.route('/syaro/swarm/search.json', methods=['GET'])
def site2():
    t = session.get('swarm', None) if not config.debug else config.debug
    ll = request.args.get('ll', None, str)
    categoryId = request.args.get('categoryId', None, str)
    if not t or not ll:
        return ''
    args = dict(oauth_token=t, m="swarm", v="20190930", radius=1000, ll=ll)
    if categoryId:
        args['categoryId'] = categoryId
    js = requests.get("https://api.foursquare.com/v2/venues/search", args).text
    g = geojsonload()
    table = []
    for x in json.loads(js)['response']['venues']:
        loc = x['location']
        d = { "type": "Feature", "geometry": { "type": "Point", "coordinates": [ loc['lng'], loc['lat'] ] } }
        g['features'].append(d)
        table.append([
            x['name'], '\n'.join([xx['name'] for xx in x['categories']])
        ])
    df = pd.DataFrame(table)
    with tempfile.TemporaryDirectory() as x:
        df.to_html(f'{x}/x.html')
        with open(f'{x}/x.html', 'r') as f:
            table = f.read()
    return make_response(jsonify(dict(geojson=g, table=table)), 200)

if __name__ == "__main__":
    app.run(debug=True, threaded=True, processes=1)

