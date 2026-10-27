import os

from sqlmodel import Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = (
        "postgresql+psycopg2://postgres.spzczfwxdjtguaurwnct:Doan_NT106."
        "@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require"
    )
engine = create_engine(DATABASE_URL, echo=True, connect_args={"sslmode": "require"})


def get_session():
    with Session(engine) as session:
        yield session
