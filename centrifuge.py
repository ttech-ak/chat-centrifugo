import json
import requests

CENTRIFUGO_API_KEY:str = ''
base = 'http://localhost:8888'

class CentrifugoPublishError(ValueError):
    pass

def centrifuge(path: str, data: str) -> dict:
    headers = {'Content-type': 'application/json', 'X-API-Key': CENTRIFUGO_API_KEY}
    resp = requests.post(base + '/api/' + path, data=data, headers=headers)
    r: dict = resp.json()
    if 'error' in r:
        raise CentrifugoPublishError(r['message'])
    return r


def publish(nick: str, chan: str, msg: str) -> dict:
    data = json.dumps({
        'channel': chan,
        'data': {
            'message': msg,
            'nick': nick,
        }
    })
    return centrifuge('publish', data)

def subscribe(nick: str, chan: str) -> dict:
    data = json.dumps({
        'user': nick,
        'channel': chan,
    })

    return centrifuge('subscribe', data)


