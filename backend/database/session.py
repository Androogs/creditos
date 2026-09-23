from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_settings


def get_database_url() -> str:
    return get_settings().sqlalchemy_database_url()


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_app_user(db: Session, id_usuario: str | None) -> None:
    """
    Establece la variable de sesión Postgres app.user_id dentro de
    la transacción actual, tal como lo exige
    database/README_AUDITORIA.md para que auditar_cambio_fila() y
    registrar_cambio_estado() registren el usuario autenticado.

    Debe llamarse ANTES de cualquier INSERT/UPDATE de la misma
    transacción sobre solicitudes, ofertas, financiaciones, pólizas,
    desembolsos o productos de aliados.

    Si id_usuario es None (petición sin usuario autenticado), no se
    hace nada: la auditoría conservará el cambio con id_usuario NULL,
    que es el comportamiento esperado según el README.
    """
    if not id_usuario:
        return

    db.execute(
        text("SET LOCAL app.user_id = :id_usuario"),
        {"id_usuario": id_usuario},
    )
