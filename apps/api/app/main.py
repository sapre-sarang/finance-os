from fastapi import FastAPI
from financeos_db.crypto import FieldCipher
from financeos_db.session import make_engine, make_session_factory

from app.config import Settings, load_settings
from app.routers import accounts, auth, imports, summary, transactions
from app.security import LoginThrottle


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="FinanceOS API", docs_url=None, redoc_url=None)

    engine = make_engine(settings.database_url.render_as_string(hide_password=False))
    app.state.settings = settings
    app.state.session_factory = make_session_factory(engine)
    app.state.cipher = FieldCipher(settings.encryption_key)
    app.state.throttle = LoginThrottle()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for module in (auth, accounts, transactions, imports, summary):
        app.include_router(module.router)
    return app
