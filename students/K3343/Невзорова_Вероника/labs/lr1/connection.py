import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator

load_dotenv()
DB_URL = os.getenv("DB_ADMIN")
engine = create_engine(DB_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session