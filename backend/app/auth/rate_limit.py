import hashlib
import math
import secrets
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select,delete,func,text
from app.database.models import LoginRateBucket
from app.auth import sessions

WINDOW=timedelta(minutes=5)
MAX_ROWS=10000


def prefixes(username,source):
    return [hashlib.sha256((kind+value).encode()).hexdigest()[:32] for kind,value in (("username:",username),("peer:",source))]


def check_limit(db,username,source):
    # Dedicated transaction lock serializes counting and recording, not the
    # admin guard. Each row is one timestamped failure; windows truly roll.
    db.execute(text("SELECT pg_advisory_xact_lock(170102)"))
    now=sessions.now_utc()
    db.execute(delete(LoginRateBucket).where(LoginRateBucket.window_start<=now-WINDOW))
    for prefix in prefixes(username,source):
        count,first=db.execute(select(func.count(),func.min(LoginRateBucket.window_start)).where(LoginRateBucket.key.like(prefix+"%"))).one()
        if count>=5:
            wait=max(1,math.ceil((first+WINDOW-now).total_seconds()))
            raise HTTPException(429,f"Thử đăng nhập lại sau {wait} giây",headers={"Retry-After":str(wait)})
    if db.scalar(select(func.count()).select_from(LoginRateBucket))>=MAX_ROWS-2:
        raise HTTPException(429,"Thử đăng nhập lại sau 300 giây",headers={"Retry-After":"300"})


def record_failure(db,username,source):
    for prefix in prefixes(username,source):
        db.add(LoginRateBucket(key=prefix+secrets.token_hex(16),window_start=sessions.now_utc(),failures=1))
    db.flush()
