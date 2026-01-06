#!/usr/bin/env python3
import argparse
from models import new_engine
from fastapi import FastAPI
import apis
import uvicorn
import json
import logging
import centrifuge

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='chat-websocket',
        description='A server to chat among multiple channels using websockets',
    )
    parser.add_argument('-p', '--port', default=8001, type=int)
    parser.add_argument('-H', '--host', default="")
    parser.add_argument('-d', '--db', default="sqlite:///db.db")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    eng, sess = new_engine(args.db)
    apis.session_maker = sess
    with open('config.json', 'r') as f:
        try:
            conf = json.load(f)
            secret = conf['client']['token']['hmac_secret_key']
            api_key = conf['http_api']['key']
        except json.JSONDecodeError:
            # can't do anything here
            raise
        except KeyError:
            # can't do anything here either
            raise
    apis.jwt_secret = secret
    centrifuge.CENTRIFUGO_API_KEY = api_key
    logger.info(f"got centrifugo secret key: {secret}")
    app = FastAPI()
    app.include_router(apis.router)
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
