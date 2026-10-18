from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from financeos_db.models import User, UserSession
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from app.deps import SESSION_COOKIE, AppSettings, CurrentUser, DbSession
from app.security import hash_token, new_session_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    username: str


@router.post("/login", response_model=UserOut)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: DbSession,
    settings: AppSettings,
) -> UserOut:
    throttle = request.app.state.throttle
    if throttle.is_blocked(body.username):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Wait a few minutes."
        )

    user = session.scalar(select(User).where(User.username == body.username))
    if not verify_password(user.password_hash if user else None, body.password) or user is None:
        throttle.record_failure(body.username)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password")

    throttle.reset(body.username)
    token = new_session_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.session_days)
    session.add(UserSession(token_hash=hash_token(token), user_id=user.id, expires_at=expires_at))
    session.commit()

    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        samesite="strict",
        secure=settings.secure_cookies,
        path="/",
    )
    return UserOut(username=user.username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, session: DbSession) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        session.execute(delete(UserSession).where(UserSession.token_hash == hash_token(token)))
        session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut(username=user.username)
