import hashlib
import secrets
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash("not-a-real-password")

MIN_PASSWORD_LENGTH = 12


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    # Verify against a dummy hash for unknown users so timing does not reveal who exists.
    try:
        return _hasher.verify(stored_hash or _DUMMY_HASH, password) and stored_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class LoginThrottle:
    """Allows a few failed sign-ins per username in a sliding window."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 300) -> None:
        self._max = max_failures
        self._window = window_seconds
        self._failures: defaultdict[str, deque[float]] = defaultdict(deque)

    def is_blocked(self, key: str) -> bool:
        failures = self._failures[key]
        cutoff = time.monotonic() - self._window
        while failures and failures[0] < cutoff:
            failures.popleft()
        return len(failures) >= self._max

    def record_failure(self, key: str) -> None:
        self._failures[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)
