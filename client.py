#!/usr/bin/env python3
import asyncio
import websockets
from websockets.asyncio.client import connect
import argparse
import requests
import json
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='chat-websocket',
        description='A server to chat among multiple channels using websockets',
    )
    parser.add_argument('-s', '--server', default="http://localhost:8001")
    parser.add_argument('-c', '--cent', default="http://localhost:8888")
    parser.add_argument('-n', '--nick', default="me")
    args = parser.parse_args()
    return args

server: str = ''
cent: str = ''
headers = {'Content-type': 'application/json'}

def api(path: str, data: dict):
    print('in api', path, data)
    resp = requests.post(server + path, data=json.dumps(data), headers=headers)
    resp_dict: dict = resp.json()
    if not resp_dict['success']:
        raise ValueError('got error ' + str(resp_dict))
    return resp_dict

def set_nick(nick: str) -> dict:
    resp = api('/set_nick', {'nick': nick})
    print("got back:", resp)
    return resp

def join_chan(chan: str) -> dict:
    resp = api(f'/join/{chan}', {})
    return resp

def send_msg(chan: str, msg: str) -> dict:
    resp = api('/msg', {'channel': chan, 'message': msg})
    return resp

def do_privmsg(msg):
    chan, msg = msg.split(maxsplit=2)
    send_msg(chan, msg)

async def handle_cent(jwt: str):
    print("in handle cent")
    async with connect('ws://localhost:8888/connection/websocket') as websocket:
        await websocket.send(json.dumps({'id': 1, 'connect': {'token': jwt}}))
        # await websocket.send(json.dumps('{}'))
        async for msg in websocket:
            if msg == '{}':
                await websocket.send('{}')
                continue
            res = json.loads(msg)
            if not 'push' in res:
                logger.info('unknown message: %s', res)
                continue
            pushed = res['push']
            if 'pub' in pushed:
                try:
                    chan = pushed['channel']
                    message = pushed['pub']['data']['message']
                    nick = pushed['pub']['data']['nick']
                    print(f'{chan}	{nick}: {message}')
                except Exception as e:
                    print('got exception', e)
            elif 'subscribe' in pushed:
                logger.info("asking for subscription on %s", pushed['channel'])
                await websocket.send(json.dumps({'id': 2, 'history': {'channel': pushed['channel'], 'limit': 10}}))
                logger.info("asked")
            else:
                print('unknown message type', msg)
            print('got', msg)
    print("leaving handle_cent")

def handle_input():
    print("in handle_input")
    line = sys.stdin.readline().strip()
    print('got line', line)
    try:
        action, msg = line.split(' ', maxsplit=1)
        match action:
            case 'nick':
                set_nick(msg)
            case 'privmsg':
                do_privmsg(msg)
            case 'join':
                join_chan(msg)
    except Exception as e:
        print('got exception', e)

async def handle_conn(jwt: str):
    print("in handle conn")
    loop = asyncio.get_running_loop()
    loop.add_reader(sys.stdin.fileno(), handle_input)
    async with asyncio.TaskGroup() as tg:
        print("started task group")
        task1 = tg.create_task(handle_cent(jwt))
        # task2 = tg.create_task(handle_input())
        print("task group should run")
    print("outside handle conn")
    

def chat(args):
    ret = set_nick(args.nick)
    obj = ret['object']
    global headers
    print('headers is: ', obj['headers'])
    print(f'{isinstance(obj["headers"], dict)=}')
    for k,v in obj['headers'].items():
        headers[k] = v

    jwt = obj['centrifugo_jwt']
    asyncio.run(handle_conn(jwt))

def main():
    args = parse_args()
    global server
    server = args.server
    global cent
    cent = args.cent
    
    chat(args)

if __name__ == "__main__":
    clogger = logging.getLogger("centrifuge")
    clogger.setLevel(logging.DEBUG)
    main()
