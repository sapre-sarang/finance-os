from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from financeos_db.crypto import FieldCipher
from financeos_db.models import User, UserSession
from sqlalchemy.orm import Session

from app.config import Settings
from app.security import hash_token

SESSION_COOKIE = "fos_session"


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_cipher(request: Request) -> FieldCipher:
    cipher: FieldCipher = request.app.state.cipher
    return cipher


def current_user(request: Request, session: DbSession) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        stored = session.get(UserSession, hash_token(token))
        if stored is not None and stored.expires_at > datetime.now(UTC):
            user = session.get(User, stored.user_id)
            if user is not None:
                return user
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue")


CurrentUser = Annotated[User, Depends(current_user)]
Cipher = Annotated[FieldCipher, Depends(get_cipher)]
AppSettings = Annotated[Settings, Depends(get_settings)]
