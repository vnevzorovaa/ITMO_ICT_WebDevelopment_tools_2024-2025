from enum import Enum
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class RaceType(str, Enum):
    director = "director"
    worker = "worker"
    junior = "junior"

class SkillWarriorLink(SQLModel, table=True):
    skill_id: Optional[int] = Field(default=None, foreign_key="skill.id", primary_key=True)
    warrior_id: Optional[int] = Field(default=None, foreign_key="warrior.id", primary_key=True)
    level: Optional[int] = Field(default=None)

class SkillBase(SQLModel):
    name: str
    description: Optional[str] = None

class Skill(SkillBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    warriors: List["Warrior"] = Relationship(back_populates="skills", link_model=SkillWarriorLink)

class SkillCreate(SkillBase):
    pass

class ProfessionBase(SQLModel):
    title: str
    description: str

class Profession(ProfessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    warriors_prof: List["Warrior"] = Relationship(back_populates="profession")

class ProfessionCreate(ProfessionBase):
    pass

class WarriorBase(SQLModel):
    race: RaceType
    name: str
    level: int
    profession_id: Optional[int] = Field(default=None, foreign_key="profession.id")

class Warrior(WarriorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profession: Optional[Profession] = Relationship(back_populates="warriors_prof")
    skills: List[Skill] = Relationship(back_populates="warriors", link_model=SkillWarriorLink)

class WarriorCreate(WarriorBase):
    pass

class WarriorRead(WarriorCreate):
    id: int
    profession: Optional[Profession] = None
    skills: List[Skill] = []
