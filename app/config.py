from dataclasses import dataclass

from environs import Env


@dataclass
class DatabaseConfig:
    database_url: str


@dataclass
class Config:
    db: DatabaseConfig
    secret_key: str
    debug: bool
    mode: str
    docs_user: str
    docs_password: str
    jwt_secret_key: str
    jwt_algorithm: str


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        db=DatabaseConfig(database_url=env("DATABASE_URL")),
        secret_key=env("SECRET_KEY"),
        debug=env.bool("DEBUG", default=False),
        mode=env.str("MODE", default="DEV"),
        docs_user=env.str("DOCS_USER", default="admin"),
        docs_password=env.str("DOCS_PASSWORD", default="admin"),
        jwt_secret_key=env.str("JWT_SECRET_KEY", default="secret"),
        jwt_algorithm=env.str("JWT_ALGORITHM", default="HS256"),
    )
