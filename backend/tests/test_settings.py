from backend.config import Settings


def test_cors_origins_are_parsed_from_csv() -> None:
    settings = Settings(
        cors_origins="http://localhost:5173, https://example.pages.dev"
    )

    assert settings.cors_origin_list() == [
        "http://localhost:5173",
        "https://example.pages.dev",
    ]


def test_sqlalchemy_url_normalizes_postgres_scheme() -> None:
    settings = Settings(
        database_url="postgresql://postgres:password@localhost:5432/creditos"
    )

    assert settings.sqlalchemy_database_url().startswith("postgresql+psycopg://")
