import time
import threading
from connection import get_session

from models import Hackathon
import requests
from bs4 import BeautifulSoup

URLS = [
    'https://codenrock.com/communities',
    'https://codenrock.com/global-rating/sport_programming',
    'https://codenrock.com/discussions'
]
NUM_WORKERS = 4

def parse_and_save(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)

    soup = BeautifulSoup(resp.text, 'html.parser')
    title = soup.title.string.strip() if soup.title else 'N/A'
    meta = soup.find('meta', attrs={'name': 'description'}) or \
           soup.find('meta', attrs={'property': 'og:description'})
    description = meta['content'].strip() if meta and meta.has_attr('content') else None

    session_gen = get_session()
    session = next(session_gen)
    hack = Hackathon(title=title, description=description)
    session.add(hack)
    session.commit()
    session.refresh(hack)
    print(f"[thread] {url} → title: {title}; desc: {description}")


def worker(urls):
    for u in urls:
        parse_and_save(u)


def main():
    seg = len(URLS) // NUM_WORKERS
    threads = []
    t0 = time.perf_counter()
    for i in range(NUM_WORKERS):
        chunk = URLS[i*seg:(i+1)*seg] if i < NUM_WORKERS-1 else URLS[i*seg:]
        t = threading.Thread(target=worker, args=(chunk,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - t0
    print(f"[threading] Time= {elapsed:.3f}s")

if __name__ == '__main__':
    main()