from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, AnyHttpUrl, ConfigDict, field_validator
from typing import List, Union
import httpx
from celery.result import AsyncResult
from .config import PARSER_SERVICE_URL
from .celery_app import app as celery_app

api = FastAPI(title="Gateway API", version="1.0")

class ParseRequest(BaseModel):
    urls: List[AnyHttpUrl]
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"urls": ["https://enter-your-url/"]}]
    })

    # разрешаем прислать одну строку вместо списка
    @field_validator("urls", mode="before")
    @classmethod
    def coerce_to_list(cls, v: Union[str, AnyHttpUrl, List[AnyHttpUrl]]):
        if isinstance(v, (str, AnyHttpUrl)):
            return [v]
        return v

@api.post("/parse/http")
async def parse_via_http(req: ParseRequest):
    payload = {"urls": [str(u) for u in req.urls]}
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(f"{PARSER_SERVICE_URL}/parse", json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Parser HTTP error: {e}")

@api.post("/parse/async")
async def parse_via_queue(req: ParseRequest):
    task = celery_app.send_task("app.tasks.parse_many_task",
                                args=[[str(u) for u in req.urls]])
    return {"task_id": task.id, "status": "PENDING"}

@api.get("/tasks/{task_id}")
async def task_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    out = {"task_id": task_id, "state": res.state}
    if res.state == "SUCCESS":
        out["result"] = res.result
    elif res.state == "FAILURE":
        out["error"] = str(res.result)
    return out