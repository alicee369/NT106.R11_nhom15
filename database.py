from sqlalchemy.engine import URL
from sqlmodel import Session, create_engine

SERVER = r"THANHMANPH"
DATABASE = "doan_nt106"

connection_url = URL.create(
    "mssql+mssqlpython",
    host=SERVER,
    database=DATABASE,
    query={
        "trusted_connection": "yes",
        "trust_server_certificate": "yes",
    },
)

engine = create_engine(connection_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session
