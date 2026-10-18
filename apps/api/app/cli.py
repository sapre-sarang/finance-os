"""Local administration: `uv run python -m app.cli migrate | create-user <username>`."""

import argparse
import getpass
import os
import sys

from alembic import command
from alembic.config import Config
from financeos_db.models import User
from financeos_db.session import make_engine, make_session_factory
from sqlalchemy import select

from app.config import REPO_ROOT, load_settings
from app.security import MIN_PASSWORD_LENGTH, hash_password


def _read_password() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.readline().rstrip("\r\n")
    password = getpass.getpass("Password: ")
    if getpass.getpass("Repeat password: ") != password:
        raise SystemExit("Passwords do not match")
    return password


def create_user(username: str) -> None:
    password = _read_password()
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    settings = load_settings()
    engine = make_engine(settings.database_url.render_as_string(hide_password=False))
    with make_session_factory(engine)() as session:
        if session.scalar(select(User).where(User.username == username)):
            raise SystemExit(f"User {username!r} already exists")
        session.add(User(username=username, password_hash=hash_password(password)))
        session.commit()
    print(f"Created user {username!r}")


def migrate() -> None:
    settings = load_settings()
    os.environ["DATABASE_URL"] = settings.database_url.render_as_string(hide_password=False)
    command.upgrade(Config(str(REPO_ROOT / "packages" / "db" / "alembic.ini")), "head")
    print("Database is up to date")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="apply database migrations")
    create = commands.add_parser("create-user", help="create the sign-in for this install")
    create.add_argument("username")
    args = parser.parse_args()
    if args.command == "migrate":
        migrate()
    elif args.command == "create-user":
        create_user(args.username)


if __name__ == "__main__":
    main()
