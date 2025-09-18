from fastapi import FastAPI, HTTPException
from typing import List
from typing_extensions import TypedDict

from models import Warrior, Profession, Skill, RaceType

app = FastAPI()

# ——— Временные "базы" ———
temp_warriors = [
    {
        "id": 1,
        "race": "director",
        "name": "Мартынов Дмитрий",
        "level": 12,
        "profession": {
            "id": 1,
            "title": "Влиятельный человек",
            "description": "Эксперт по всем вопросам"
        },
        "skills": [
            {"id": 1, "name": "Купле-продажа компрессоров", "description": ""},
            {"id": 2, "name": "Оценка имущества",           "description": ""}
        ]
    },
    {
        "id": 2,
        "race": "worker",
        "name": "Андрей Косякин",
        "level": 12,
        "profession": {
            "id": 2,
            "title": "Дельфист-гребец",
            "description": "Уважаемый сотрудник"
        },
        "skills": []
    },
]

temp_professions = [
    {"id": 1, "title": "Влиятельный человек", "description": "Эксперт по всем вопросам"},
    {"id": 2, "title": "Дельфист-гребец",     "description": "Уважаемый сотрудник"},
]

# ——— API для воинов ———
@app.get("/")
async def read_root():
    return {"message": "API is running"}


@app.get("/warriors_list", response_model=List[Warrior])
def warriors_list():
    return temp_warriors

@app.get("/warrior/{warrior_id}", response_model=Warrior)
def warriors_get(warrior_id: int):
    for w in temp_warriors:
        if w["id"] == warrior_id:
            return w
    raise HTTPException(status_code=404, detail="Warrior not found")

class WarriorResponse(TypedDict):
    status: int
    data: Warrior

@app.post("/warrior", response_model=WarriorResponse)
def warriors_create(warrior: Warrior):
    temp_warriors.append(warrior.model_dump())
    return {"status": 200, "data": warrior}

@app.delete("/warrior/{warrior_id}")
def warrior_delete(warrior_id: int):
    for i, w in enumerate(temp_warriors):
        if w["id"] == warrior_id:
            temp_warriors.pop(i)
            return {"status": 201, "message": "deleted"}
    raise HTTPException(status_code=404, detail="Warrior not found")

@app.put("/warrior/{warrior_id}", response_model=List[Warrior])
def warrior_update(warrior_id: int, warrior: Warrior):
    for i, w in enumerate(temp_warriors):
        if w["id"] == warrior_id:
            temp_warriors[i] = warrior.model_dump()
            return temp_warriors
    raise HTTPException(status_code=404, detail="Warrior not found")


# ——— API для профессий ———
@app.get("/professions", response_model=List[Profession])
def professions_list():
    return temp_professions

@app.get("/profession/{profession_id}", response_model=Profession)
def profession_get(profession_id: int):
    for p in temp_professions:
        if p["id"] == profession_id:
            return p
    raise HTTPException(status_code=404, detail="Profession not found")

class ProfessionResponse(TypedDict):
    status: int
    data: Profession

@app.post("/profession", response_model=ProfessionResponse)
def profession_create(profession: Profession):
    temp_professions.append(profession.model_dump())
    return {"status": 200, "data": profession}

@app.delete("/profession/{profession_id}")
def profession_delete(profession_id: int):
    for i, p in enumerate(temp_professions):
        if p["id"] == profession_id:
            temp_professions.pop(i)
            return {"status": 201, "message": "deleted"}
    raise HTTPException(status_code=404, detail="Profession not found")

@app.put("/profession/{profession_id}", response_model=List[Profession])
def profession_update(profession_id: int, profession: Profession):
    for i, p in enumerate(temp_professions):
        if p["id"] == profession_id:
            temp_professions[i] = profession.model_dump()
            return temp_professions
    raise HTTPException(status_code=404, detail="Profession not found")