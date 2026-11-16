"""Shared request dependencies."""

from __future__ import annotations

import re
import uuid

from fastapi import Request, Response

from app.config import COOKIE_MAX_AGE, COOKIE_NAME, COOKIE_SECURE

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def client_id(request: Request, response: Response) -> str:
    """Anonymous id for this browser, kept in an http-only cookie.

    There are no accounts: a browser can only see the checks it made itself.
    """
    cid = request.cookies.get(COOKIE_NAME, "")
    if not _UUID.match(cid):
        cid = str(uuid.uuid4())
        response.set_cookie(
            COOKIE_NAME, cid, max_age=COOKIE_MAX_AGE, httponly=True, samesite="lax", secure=COOKIE_SECURE
        )
    return cid
