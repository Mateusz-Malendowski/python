import requests
import json
import re
from flask import Flask
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['CORS_HEADERS'] = 'Content-Type'

CLIENT_ID = "client id from twitch's api"
SECRET = "secret from twitch's api"
USER_ID = "twitch id of user"
USER_LOGIN = "twitch login of user"

@app.route('/')
@cross_origin()
def hello_world():
    sk = "https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials".format(CLIENT_ID, SECRET)
    ra = requests.post(sk)
    atd = ra.json()

    fvu = "https://api.twitch.tv/helix/videos?user_id={}&first=1&sort=time&type=archive".format(USER_ID)
    rb= requests.get(fvu, headers={"Client-ID":CLIENT_ID, 'Authorization': "Bearer "+atd["access_token"]})

    resp=json.dumps( rb.json(), indent = 4)

    r = re.search("\"id\": \"(\d*)\"",resp);

    cl = "https://api.twitch.tv/helix/streams?user_login={}".format(USER_LOGIN)
    rc= requests.get(cl, headers={"Client-ID":CLIENT_ID, 'Authorization': "Bearer "+atd["access_token"]})

    resp=rc.json()

    if len(resp['data']) == 1:
        return r.group(1)+" true"
    else:
        return r.group(1)+" false"

