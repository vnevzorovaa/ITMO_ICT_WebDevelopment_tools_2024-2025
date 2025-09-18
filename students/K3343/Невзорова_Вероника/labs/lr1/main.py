from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from sqlmodel import select, Session
from connection import init_db, get_session
import jwt, hashlib, os
from datetime import datetime, timedelta


from models import (
    Hackathon, HackathonCreate, HackathonRead,
    Team, TeamCreate, TeamRead,
    Problem, ProblemCreate,
    Submission, SubmissionCreate, SubmissionRead,
    User
)

# JWT settings
SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
security = HTTPBearer()

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()


# --- AuthService ---

class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def get_password_hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)

    def register(self, username: str, email: str, password: str):
        hashed = self.get_password_hash(password)
        user = User(username=username, email=email, hashed_password=hashed)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str):
        user = self.session.exec(select(User).where(User.username == username)).first()
        if not user or user.hashed_password != self.get_password_hash(password):
            return None
        return user

    def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> User:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if not username:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except jwt.PyJWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        user = self.session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    def change_password(self, current_user: User, old_password: str, new_password: str):
        if current_user.hashed_password != self.get_password_hash(old_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong old password")
        current_user.hashed_password = self.get_password_hash(new_password)
        self.session.add(current_user)
        self.session.commit()


# --- HackathonService ---

class HackathonService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, hack_in: HackathonCreate) -> HackathonRead:
        hack = Hackathon(**hack_in.model_dump())
        self.session.add(hack)
        self.session.commit()
        self.session.refresh(hack)
        return self.session.get(Hackathon, hack.id)

    def read_all(self) -> List[HackathonRead]:
        return self.session.exec(select(Hackathon)).all()

    def read(self, hackathon_id: int) -> HackathonRead:
        hack = self.session.get(Hackathon, hackathon_id)
        if not hack:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
        return hack

    def update(self, hackathon_id: int, hack_update: HackathonCreate) -> HackathonRead:
        hack = self.session.get(Hackathon, hackathon_id)
        if not hack:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
        data = hack_update.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(hack, k, v)
        self.session.add(hack)
        self.session.commit()
        self.session.refresh(hack)
        return hack

    def delete(self, hackathon_id: int):
        hack = self.session.get(Hackathon, hackathon_id)
        if not hack:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        self.session.delete(hack)
        self.session.commit()


# --- TeamService ---

class TeamService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, team_in: TeamCreate) -> Team:
        hack = self.session.get(Hackathon, team_in.hackathon_id)
        if not hack:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hackathon {team_in.hackathon_id} not found")

        team = Team(name=team_in.name, hackathon_id=team_in.hackathon_id)
        self.session.add(team)
        self.session.commit()
        self.session.refresh(team)

        for user_id in team_in.members:
            user = self.session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
            link = TeamMemberLink(team_id=team.id, user_id=user_id, role="member")
            self.session.add(link)

        self.session.commit()
        self.session.refresh(team)
        return team

    def read_all(self) -> List[TeamRead]:
        return self.session.exec(select(Team)).all()

    def read(self, team_id: int) -> TeamRead:
        team = self.session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        return team

    def update(self, team_id: int, team_update: TeamCreate) -> TeamRead:
        team = self.session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        data = team_update.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(team, k, v)
        self.session.add(team)
        self.session.commit()
        self.session.refresh(team)
        return team

    def delete(self, team_id: int):
        team = self.session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        self.session.delete(team)
        self.session.commit()


# --- ProblemService ---

class ProblemService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, prob_in: ProblemCreate) -> Problem:
        prob = Problem(**prob_in.model_dump())
        self.session.add(prob)
        self.session.commit()
        self.session.refresh(prob)
        return prob

    def read_all(self) -> List[Problem]:
        return self.session.exec(select(Problem)).all()

    def read(self, problem_id: int) -> Problem:
        prob = self.session.get(Problem, problem_id)
        if not prob:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        return prob

    def update(self, problem_id: int, prob_update: ProblemCreate) -> Problem:
        prob = self.session.get(Problem, problem_id)
        if not prob:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        data = prob_update.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(prob, k, v)
        self.session.add(prob)
        self.session.commit()
        self.session.refresh(prob)
        return prob

    def delete(self, problem_id: int):
        prob = self.session.get(Problem, problem_id)
        if not prob:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        self.session.delete(prob)
        self.session.commit()


# --- SubmissionService ---

class SubmissionService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, sub_in: SubmissionCreate) -> SubmissionRead:
        sub = Submission(**sub_in.model_dump())
        self.session.add(sub)
        self.session.commit()
        self.session.refresh(sub)
        return sub

    # Добавь остальные методы по аналогии, если нужно...


# --- Routes ---

def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(session)

def get_hackathon_service(session: Session = Depends(get_session)) -> HackathonService:
    return HackathonService(session)

def get_team_service(session: Session = Depends(get_session)) -> TeamService:
    return TeamService(session)

def get_problem_service(session: Session = Depends(get_session)) -> ProblemService:
    return ProblemService(session)

def get_submission_service(session: Session = Depends(get_session)) -> SubmissionService:
    return SubmissionService(session)


# Auth routes
@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(username: str, email: str, password: str, auth_service: AuthService = Depends(get_auth_service)):
    auth_service.register(username, email, password)
    return {"msg": "Registered"}


@app.post("/auth/login")
def login(username: str, password: str, auth_service: AuthService = Depends(get_auth_service)):
    user = auth_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = auth_service.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/change-password")
def change_password(old_password: str, new_password: str,
                    credentials: HTTPAuthorizationCredentials = Depends(security),
                    auth_service: AuthService = Depends(get_auth_service)):
    current_user = auth_service.get_current_user(credentials)
    auth_service.change_password(current_user, old_password, new_password)
    return {"msg": "Password changed"}


# Hackathon routes
@app.post("/hackathons", response_model=HackathonRead)
def create_hackathon(hack_in: HackathonCreate, hack_service: HackathonService = Depends(get_hackathon_service)):
    return hack_service.create(hack_in)

@app.get("/hackathons", response_model=List[HackathonRead])
def list_hackathons(hack_service: HackathonService = Depends(get_hackathon_service)):
    return hack_service.read_all()

@app.get("/hackathons/{hackathon_id}", response_model=HackathonRead)
def get_hackathon(hackathon_id: int, hack_service: HackathonService = Depends(get_hackathon_service)):
    return hack_service.read(hackathon_id)

@app.put("/hackathons/{hackathon_id}", response_model=HackathonRead)
def update_hackathon(hackathon_id: int, hack_in: HackathonCreate, hack_service: HackathonService = Depends(get_hackathon_service)):
    return hack_service.update(hackathon_id, hack_in)

@app.delete("/hackathons/{hackathon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hackathon(hackathon_id: int, hack_service: HackathonService = Depends(get_hackathon_service)):
    hack_service.delete(hackathon_id)
    return {}

@app.post("/teams/", response_model=Team)
def create_team(team: TeamCreate, session: Session = Depends(get_session)):
    db_team = Team(name=team.name, hackathon_id=team.hackathon_id)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)

    # Привязать участников к команде
    for user_id in team.members:
        assoc = TeamUserAssociation(team_id=db_team.id, user_id=user_id, role="member")
        session.add(assoc)
    session.commit()

    return db_team

@app.get("/teams/", response_model=List[Team])
def read_teams(session: Session = Depends(get_session)):
    return session.exec(select(Team)).all()


@app.get("/teams/{team_id}", response_model=TeamRead)
def get_team(team_id: int, team_service: TeamService = Depends(get_team_service)):
    return team_service.read(team_id)

@app.put("/teams/{team_id}", response_model=TeamRead)
def update_team(team_id: int, team_in: TeamCreate, team_service: TeamService = Depends(get_team_service)):
    return team_service.update(team_id, team_in)

@app.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, team_service: TeamService = Depends(get_team_service)):
    team_service.delete(team_id)
    return {}

@app.post("/problems/", response_model=Problem)
def create_problem(problem: ProblemCreate, session: Session = Depends(get_session)):
    db_problem = Problem(**problem.dict())
    session.add(db_problem)
    session.commit()
    session.refresh(db_problem)
    return db_problem

@app.get("/problems/", response_model=List[Problem])
def read_problems(session: Session = Depends(get_session)):
    return session.exec(select(Problem)).all()

@app.put("/problems/{problem_id}", response_model=Problem)
def update_problem(problem_id: int, problem_in: ProblemCreate, problem_service: ProblemService = Depends(get_problem_service)):
    return problem_service.update(problem_id, problem_in)

@app.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(problem_id: int, problem_service: ProblemService = Depends(get_problem_service)):
    problem_service.delete(problem_id)
    return {}


# Submission routes
@app.post("/submissions", response_model=SubmissionRead)
def create_submission(submission_in: SubmissionCreate, submission_service: SubmissionService = Depends(get_submission_service)):
    return submission_service.create(submission_in)

@app.get("/submissions", response_model=List[SubmissionRead])
def list_submissions(submission_service: SubmissionService = Depends(get_submission_service)):
    return submission_service.read_all()

@app.get("/submissions/{submission_id}", response_model=SubmissionRead)
def get_submission(submission_id: int, submission_service: SubmissionService = Depends(get_submission_service)):
    return submission_service.read(submission_id)

@app.put("/submissions/{submission_id}", response_model=SubmissionRead)
def update_submission(submission_id: int, submission_in: SubmissionCreate, submission_service: SubmissionService = Depends(get_submission_service)):
    return submission_service.update(submission_id, submission_in)

@app.delete("/submissions/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(submission_id: int, submission_service: SubmissionService = Depends(get_submission_service)):
    submission_service.delete(submission_id)
    return {}

SECRET = "supersecretkey"
ALGORITHM = "HS256"