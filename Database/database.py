import os

from sqlmodel import Session, create_engine

SUPABASE_URL = "postgresql+psycopg2://postgres.spzczfwxdjtguaurwnct:Doan_NT106.@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

DATABASE_URL = os.getenv("DATABASE_URL", SUPABASE_URL)

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


# pw_supabase: Doan_NT106@
