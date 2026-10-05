from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from app.auth import sessions
from app.database.models import Account, AuthSession

START=datetime(2026,1,1,tzinfo=timezone.utc)


@pytest.mark.parametrize("deadline",["idle","absolute"])
@pytest.mark.parametrize("offset",[-1,0,1])
def test_cutoffs_one_microsecond_before_at_after(monkeypatch,deadline,offset):
    boundary=START+timedelta(minutes=30) if deadline=="idle" else START+timedelta(hours=8)
    now=boundary+timedelta(microseconds=offset)
    row=AuthSession(token_digest=sessions.digest("token"),csrf_digest=sessions.digest("csrf"),created_at=START,
                    last_activity_at=START if deadline=="idle" else boundary-timedelta(minutes=1))
    account=Account(role="technician",active=True)
    db=MagicMock();db.execute.return_value.scalar_one_or_none.side_effect=[row,account]
    monkeypatch.setattr(sessions,"now_utc",lambda:now)
    if offset<0:
        assert sessions.resolve_session(db,"token")== (row,account)
    else:
        with pytest.raises(HTTPException) as error:
            sessions.resolve_session(db,"token")
        assert error.value.status_code==401


def test_independent_sessions_and_absolute_never_extends(monkeypatch):
    account=Account(role="technician",active=True)
    now=START+timedelta(hours=8)
    old=AuthSession(created_at=START,last_activity_at=now-timedelta(seconds=1))
    new=AuthSession(created_at=now-timedelta(minutes=5),last_activity_at=now-timedelta(minutes=5))
    monkeypatch.setattr(sessions,"now_utc",lambda:now)
    expired_db=MagicMock();expired_db.execute.return_value.scalar_one_or_none.side_effect=[old,account]
    with pytest.raises(HTTPException):sessions.resolve_session(expired_db,"old-token")
    fresh_db=MagicMock();fresh_db.execute.return_value.scalar_one_or_none.side_effect=[new,account]
    assert sessions.resolve_session(fresh_db,"new-token")[0] is new
