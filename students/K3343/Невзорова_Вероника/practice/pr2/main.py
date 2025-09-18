from fastapi import FastAPI, Depends, HTTPException
from typing import List
from sqlmodel import select

from connection import init_db, get_session
from models import (
    Warrior, WarriorCreate, WarriorRead,
    Profession, ProfessionCreate,
    Skill, SkillCreate
)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

# warriors
@app.post("/warrior", response_model=WarriorRead)
def create_warrior(warrior: WarriorCreate, session=Depends(get_session)):
    db_warrior = Warrior.model_validate(warrior)
    session.add(db_warrior)
    session.commit()
    session.refresh(db_warrior)
    return db_warrior

@app.get("/warriors_list", response_model=List[WarriorRead])
def warriors_list(session=Depends(get_session)):
    return session.exec(select(Warrior)).all()

@app.get("/warrior/{warrior_id}", response_model=WarriorRead)
def warrior_get(warrior_id: int, session=Depends(get_session)):
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    return warrior

@app.patch("/warrior/{warrior_id}", response_model=WarriorRead)
def warrior_update(warrior_id: int, warrior: WarriorCreate, session=Depends(get_session)):
    db_warrior = session.get(Warrior, warrior_id)
    if not db_warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    warrior_data = warrior.model_dump(exclude_unset=True)
    for key, value in warrior_data.items():
        setattr(db_warrior, key, value)
    session.add(db_warrior)
    session.commit()
    session.refresh(db_warrior)
    return db_warrior

@app.delete("/warrior/delete/{warrior_id}")
def warrior_delete(warrior_id: int, session=Depends(get_session)):
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    session.delete(warrior)
    session.commit()
    return {"ok": True}

# professions
@app.post("/profession", response_model=Profession)
def create_profession(prof: ProfessionCreate, session=Depends(get_session)):
    db_prof = Profession.model_validate(prof)
    session.add(db_prof)
    session.commit()
    session.refresh(db_prof)
    return db_prof

@app.get("/professions_list", response_model=List[Profession])
def professions_list(session=Depends(get_session)):
    return session.exec(select(Profession)).all()

@app.get("/profession/{profession_id}", response_model=Profession)
def profession_get(profession_id: int, session=Depends(get_session)):
    prof = session.get(Profession, profession_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profession not found")
    return prof

@app.delete("/profession/delete/{profession_id}")
def profession_delete(profession_id: int, session=Depends(get_session)):
    prof = session.get(Profession, profession_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profession not found")
    session.delete(prof)
    session.commit()
    return {"ok": True}

# skills
@app.post("/skill", response_model=Skill)
def create_skill(skill: SkillCreate, session=Depends(get_session)):
    db_skill = Skill.model_validate(skill)
    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return db_skill

@app.get("/skills_list", response_model=List[Skill])
def skills_list(session=Depends(get_session)):
    return session.exec(select(Skill)).all()

@app.get("/skill/{skill_id}", response_model=Skill)
def skill_get(skill_id: int, session=Depends(get_session)):
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@app.delete("/skill/delete/{skill_id}")
def skill_delete(skill_id: int, session=Depends(get_session)):
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    session.delete(skill)
    session.commit()
    return {"ok": True}
