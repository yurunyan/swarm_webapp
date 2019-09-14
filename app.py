from flask import Flask, request, render_template, redirect, session, escape
from downloads import config
import requests, json, os
from uuid import uuid4

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/syaro/swarm/', methods=['GET'])
def site_home():
    code = request.args.get('code', None)
    token = os.environ.get('swarm', None)
    g = geojsonload()
    if code:
        if not token:
            url = "https://foursquare.com/oauth2/access_token?" + \
                f"client_id={config.app['key']}&client_secret={config.app['secret']}" + \
                f"&grant_type=authorization_code&redirect_uri={config.app['redirect']}&code={code}"
            token = json.loads(requests.get(url).text)["access_token"]
            os.environ['swarm'] = token
    js = requests.get("https://api.foursquare.com/v2/venues/search", dict(
        oauth_token=token,
        m="swarm",
        v="20190930",
        radius=1000,
        ll="35.474834,139.367800"
    )).text
    for x in json.loads(js)['response']['venues']:
        loc = x['location']
        d = { "type": "Feature", "geometry": { "type": "Point", "coordinates": [ loc['lng'], loc['lat'] ] } }
        g['features'].append(d)
    return render_template('swarm/index.html', app=config.app, g=json.dumps(g))
    # js=json.dumps(js, indent=2, ensure_ascii=False)
def geojsonload():
    res = {
        "type": "FeatureCollection",
        "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
        "features": []
    }
    return res

if __name__ == "__main__":
    app.run(debug=True, threaded=True, processes=1)

