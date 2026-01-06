from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Annotated, Any
import sqlalchemy.orm as sorm
from pydantic import BaseModel
import models
import centrifuge_api as centrifuge
import jwt
import time


class NickJson(BaseModel):
    nick: str

class Message(BaseModel):
    channel: str
    message: str

router = APIRouter()
session_maker: None|sorm.sessionmaker = None
jwt_secret: str = ''

def get_db() -> sorm.sessionmaker:
    global session_maker
    if session_maker is None:
        raise HTTPException(status_code=500, detail='NO db set!')
    return session_maker

dbDep = Annotated[sorm.sessionmaker, Depends(get_db)]


def nick_getter(authorization: Annotated[str | None, Header()] = None) -> str:
    if authorization is None:
        raise HTTPException(status_code=424, detail='No nick set!')
    nick = authorization.removeprefix('bearer ')
    return nick
nickDep = Annotated[str, Depends(nick_getter)]

def resp(succ: bool, msg: str, obj: Any = None):
    if obj is None:
        return {'success': succ, 'message': msg}
    return {'success': succ, 'message': msg, 'object': obj}


def get_jwt(nick) -> str:
    token = jwt.encode({"sub": nick, "exp": int(time.time()) + 10*60},
                       jwt_secret, algorithm="HS256")
    return token

@router.post('/set_nick')
def set_nick(nj: NickJson, db: dbDep):
    """
    1. add user to db
    2. send jwt token to client
    3. client connects to centrifugo with the token.
    """
    with db.begin() as sess:
        models.add_nick(sess, nj.nick)
    return resp(True, f'nick set to {nj.nick}',
                {
                    'headers': {'authorization': f'bearer {nj.nick}'},
                    'centrifugo_jwt': get_jwt(nj.nick),
                 })

@router.post('/join/{chan}')
def join_chan(chan: str, nick: nickDep):
    centrifuge.subscribe(nick, chan)
    return resp(True, f'joined {chan}')

@router.post('/msg')
def msg_chan(msg: Message, nick: nickDep, db: dbDep):
    with db.begin() as sess:
        models.new_log(sess, nick, msg.channel, msg.message)
        centrifuge.publish(nick, msg.channel, msg.message)
    return resp(True, f'posted message by {nick}')
