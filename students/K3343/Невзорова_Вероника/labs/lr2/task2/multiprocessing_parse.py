import time
from multiprocessing import Pool
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
#from Невзорова_Вероника.labs.lr1.models import Hackathon
from models import Hackathon

URLS = [
    'https://codenrock.com/communities',
    'https://codenrock.com/global-rating/sport_programming',
    'https://codenrock.com/discussions'
]
NUM_WORKERS = 4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}

load_dotenv()
DB_URL = os.getenv("DB_ADMIN")

engine = create_engine(
    DB_URL,
    echo=True,
    pool_pre_ping=True,
    poolclass=NullPool
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

init_db()

def parse_and_save(url: str):
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"[proc] Ошибка {resp.status_code} при запросе {url}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    title = soup.title.string.strip() if soup.title else None
    meta = soup.find('meta', attrs={'name': 'description'}) or \
           soup.find('meta', attrs={'property': 'og:description'})
    description = meta['content'].strip() if meta and meta.has_attr('content') else None

    # Контекст new-сессии для каждого процесса
    session_gen = get_session()
    session = next(session_gen)
    try:
        hack = Hackathon(title=title or 'N/A', description=description)
        session.add(hack)
        session.commit()
        session.refresh(hack)
    finally:
        session_gen.close()

    print(f"[proc] {url} → title: {title!r}; desc: {description!r}")

def main():
    t0 = time.perf_counter()
    with Pool(NUM_WORKERS) as pool:
        pool.map(parse_and_save, URLS)
    print(f"[multiprocessing] Time= {time.perf_counter() - t0:.3f}s")

if __name__ == '__main__':
    main()