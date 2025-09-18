import os
import time
import asyncio
import socket
import aiohttp
import asyncpg
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel, AnyHttpUrl, ConfigDict, field_validator
from typing import List, Union, Optional

load_dotenv()

DB_DSN = os.getenv("DB_ADMIN")
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}


async def fetch_html(session: aiohttp.ClientSession, url: str):
    try:
        async with session.get(url, headers=HEADERS, ssl=False) as resp:
            text = await resp.text()
            return resp.status, text
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"

async def parse_and_save(url: str, http: aiohttp.ClientSession, pg_pool: asyncpg.Pool):
    status, data = await fetch_html(http, url)

    if status != 200:
        print(f"[async] Ошибка при запросе {url}: {data}")
        return {"url": url, "status": status, "title": None, "description": None, "error": data}

    html = data
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else None
    meta = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    description = meta["content"].strip() if meta and meta.has_attr("content") else None

    try:
        async with pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO hackathon (title, description)
                VALUES ($1, $2)
                """,
                title or "N/A",
                description,
            )
    except Exception as e:
        # Ошибки БД не должны рушить весь запрос
        err = f"{type(e).__name__}: {e}"
        print(f"[async] DB error for {url}: {err}")
        return {
            "url": url,
            "status": 200,
            "title": title,
            "description": description,
            "error": err,
        }

    print(f"[async] {url} → title: {title!r}; desc: {description!r}")
    return {"url": url, "status": 200, "title": title, "description": description}


async def run_parse(urls: List[str], db_dsn: Optional[str] = None, num_workers: Optional[int] = None) -> dict:
    """Общая функция парсинга: используется и HTTP-эндпоинтом, и Celery-задачами."""
    dsn = db_dsn or DB_DSN
    if not dsn:
        raise RuntimeError("DB_ADMIN не задан в окружении")
    workers = num_workers or NUM_WORKERS

    t0 = time.perf_counter()
    pg_pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,
        max_size=min(workers, max(1, len(urls))),
        max_inactive_connection_lifetime=30,
    )

    connector = aiohttp.TCPConnector(family=socket.AF_INET)  # принудительно IPv4
    timeout = aiohttp.ClientTimeout(total=60)

    results: List[dict] = []
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, trust_env=True) as http:
            sem = asyncio.Semaphore(workers)

            async def worker(u: str):
                async with sem:
                    res = await parse_and_save(u, http, pg_pool)
                    results.append(res)

            await asyncio.gather(*(worker(u) for u in urls))
    finally:
        await pg_pool.close()

    return {
        "message": "Parsing completed",
        "count": len(urls),
        "elapsed_sec": round(time.perf_counter() - t0, 3),
        "items": results,
    }

# --- обёртка, которую ждут Celery-задачи ---
async def parse_urls(urls: List[str], db_dsn: str, num_workers: int):
    return await run_parse(urls, db_dsn=db_dsn, num_workers=num_workers)

# ====== FastAPI слой ======
class ParseIn(BaseModel):
    urls: List[AnyHttpUrl]
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"urls": ["https://example.com/"]}]
    })

    @field_validator("urls", mode="before")
    @classmethod
    def coerce_to_list(cls, v: Union[str, AnyHttpUrl, List[AnyHttpUrl]]):
        if isinstance(v, (str, AnyHttpUrl)):
            return [v]
        return v

app = FastAPI(title="Parser API", version="1.0")
@app.post("/parse")
async def parse_endpoint(payload: ParseIn):
    urls = [str(u) for u in payload.urls]
    urls = list(dict.fromkeys(urls))  # уникализируем
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    try:
        return await run_parse(urls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")