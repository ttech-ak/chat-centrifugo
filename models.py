from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
import sqlalchemy as sa
import sqlalchemy.orm as sorm
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Nick(Base):
    __tablename__ = "nick"

    nick: Mapped[str] = mapped_column(primary_key=True)
    last_seen: Mapped[datetime] = mapped_column(sa.DATETIME, server_default=sa.func.now())

    def __repr__(self) -> str:
        nick, last_seen = self.nick, self.last_seen
        return f"Nick({nick=!r}, {last_seen=!r})"

class Log(Base):
    __tablename__ = "log"
    lid: Mapped[str] = mapped_column(primary_key=True)
    nick: Mapped[str] = mapped_column(sa.ForeignKey("nick.nick"))
    msg: Mapped[str] = mapped_column(String(512))
    chan: Mapped[str] = mapped_column(String(64))
    timestamp: Mapped[datetime] = mapped_column(sa.DATETIME, server_default=sa.func.now())
    def __repr__(self) -> str:
        lid, nick, msg, timestamp = self.lid, self.nick, self.msg, self.timestamp
        return f"Log({lid=!r}, {nick=!r}, {msg=!r}, {timestamp=!r})"

def add_nick(db: sorm.Session, nick):
    db.execute(sqlite_insert(Nick).on_conflict_do_nothing(), {"nick": nick})

def new_log(db, nick: str, chan: str, msg: str):
    l = Log(nick=nick, chan=chan, msg=msg)
    db.add(l)

def new_engine(dburl: str):
    engine = sa.create_engine(dburl, echo=True)
    session = sorm.sessionmaker(engine)

    Base.metadata.create_all(engine)

    return engine, session
