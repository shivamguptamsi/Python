"""
JEEnius — FastAPI Backend
Run: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid


app = FastAPI(
    title="JEEnius API",
    description="Backend for the JEEnius JEE Prep Platform",
    version="1.0.0",
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ─── In-memory DB (replace with PostgreSQL / MongoDB in prod) ─────────────────
users_db: dict = {}
questions_db: dict = {}
attempts_db: list = []
notes_db: dict = {}
leaderboard_db: list = []

# Seed some questions
seed_questions = [
    {"id": "q1", "subject": "Physics", "chapter": "Mechanics", "difficulty": "medium",
     "text": "A particle moves in a circle of radius R with constant speed v. What is the magnitude of change in velocity when the particle moves through 90°?",
     "choices": ["v√2", "2v", "v/√2", "v"], "answer": 0, "year": 2023, "source": "JEE Advanced"},
    {"id": "q2", "subject": "Chemistry", "chapter": "Organic", "difficulty": "hard",
     "text": "Which of the following has the highest electron affinity?",
     "choices": ["F", "Cl", "O", "S"], "answer": 1, "year": 2022, "source": "JEE Mains"},
    {"id": "q3", "subject": "Mathematics", "chapter": "Calculus", "difficulty": "medium",
     "text": "∫₀^π sin(x) dx equals:",
     "choices": ["0", "1", "2", "π"], "answer": 2, "year": 2024, "source": "JEE Mains"},
    {"id": "q4", "subject": "Physics", "chapter": "Electrostatics", "difficulty": "easy",
     "text": "A body is projected with velocity u at angle θ. The range is maximum when θ equals:",
     "choices": ["30°", "45°", "60°", "90°"], "answer": 1, "year": 2021, "source": "JEE Advanced"},
]
for q in seed_questions:
    questions_db[q["id"]] = q

# ─── Schemas ──────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    cls: str  # "Class 11", "Class 12", "Dropper"
    password: str

class UserOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    cls: str
    plan: str
    streak: int
    total_questions: int
    accuracy: float
    rank: Optional[int]
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class QuizAttempt(BaseModel):
    question_id: str
    selected: int
    time_taken: int  # seconds

class AttemptResult(BaseModel):
    correct: bool
    correct_answer: int
    explanation: Optional[str] = None

class SessionResult(BaseModel):
    session_id: str
    total: int
    correct: int
    wrong: int
    accuracy: float
    time_taken: int

class NoteCreate(BaseModel):
    title: str
    body: str
    subject: Optional[str] = None
    chapter: Optional[str] = None
    tags: Optional[List[str]] = []

class NoteOut(BaseModel):
    id: str
    title: str
    body: str
    subject: Optional[str]
    chapter: Optional[str]
    tags: List[str]
    created_at: str
    updated_at: str

class QuestionFilter(BaseModel):
    subject: Optional[str] = None
    chapter: Optional[str] = None
    difficulty: Optional[str] = None
    year: Optional[int] = None
    source: Optional[str] = None
    count: int = 10

# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    cred_exc = HTTPException(status_code=401, detail="Invalid credentials",
                             headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = users_db.get(email)
    if not user:
        raise cred_exc
    return user

def user_to_out(u: dict) -> UserOut:
    return UserOut(
        id=u["id"], first_name=u["first_name"], last_name=u["last_name"],
        email=u["email"], phone=u["phone"], cls=u["cls"], plan=u["plan"],
        streak=u["streak"], total_questions=u["total_questions"],
        accuracy=u["accuracy"], rank=u.get("rank"), created_at=u["created_at"]
    )

# ─── Routes ───────────────────────────────────────────────────────────────────

# Static files
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("index.html")

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/auth/register", response_model=Token, tags=["Auth"])
async def register(data: UserCreate):
    if data.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "phone": data.phone,
        "cls": data.cls,
        "password": hash_password(data.password),
        "plan": "free",
        "streak": 0,
        "total_questions": 0,
        "accuracy": 0.0,
        "rank": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    users_db[data.email] = user
    token = create_access_token({"sub": data.email},
                                 timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=token, token_type="bearer", user=user_to_out(user))

@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form.username)
    if not user or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": form.username},
                                 timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=token, token_type="bearer", user=user_to_out(user))

@app.get("/auth/me", response_model=UserOut, tags=["Auth"])
async def get_me(current_user: dict = Depends(get_current_user)):
    return user_to_out(current_user)

# ── Questions ─────────────────────────────────────────────────────────────────
@app.get("/questions", tags=["Questions"])
async def list_questions(
    subject: Optional[str] = None,
    chapter: Optional[str] = None,
    difficulty: Optional[str] = None,
    year: Optional[int] = None,
    count: int = 10,
    current_user: dict = Depends(get_current_user)
):
    qs = list(questions_db.values())
    if subject:
        qs = [q for q in qs if q["subject"].lower() == subject.lower()]
    if chapter:
        qs = [q for q in qs if q["chapter"].lower() == chapter.lower()]
    if difficulty:
        qs = [q for q in qs if q["difficulty"].lower() == difficulty.lower()]
    if year:
        qs = [q for q in qs if q.get("year") == year]
    # Hide correct answer from response
    return [{"id": q["id"], "subject": q["subject"], "chapter": q["chapter"],
             "difficulty": q["difficulty"], "text": q["text"],
             "choices": q["choices"], "year": q.get("year"),
             "source": q.get("source")} for q in qs[:count]]

@app.post("/questions/{question_id}/attempt", response_model=AttemptResult, tags=["Questions"])
async def attempt_question(
    question_id: str,
    attempt: QuizAttempt,
    current_user: dict = Depends(get_current_user)
):
    q = questions_db.get(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    correct = attempt.selected == q["answer"]
    # Update user stats
    user = users_db[current_user["email"]]
    user["total_questions"] += 1
    attempts_db.append({
        "user_id": user["id"],
        "question_id": question_id,
        "selected": attempt.selected,
        "correct": correct,
        "time_taken": attempt.time_taken,
        "timestamp": datetime.utcnow().isoformat()
    })
    # Recalculate accuracy
    user_attempts = [a for a in attempts_db if a["user_id"] == user["id"]]
    if user_attempts:
        user["accuracy"] = round(
            sum(1 for a in user_attempts if a["correct"]) / len(user_attempts) * 100, 1
        )
    return AttemptResult(
        correct=correct,
        correct_answer=q["answer"],
        explanation=f"The correct answer is option {q['answer']+1}. Review this concept in your notes."
    )

# ── Sessions (Quiz) ────────────────────────────────────────────────────────────
@app.post("/sessions/complete", response_model=SessionResult, tags=["Sessions"])
async def complete_session(
    attempts: List[QuizAttempt],
    current_user: dict = Depends(get_current_user)
):
    session_id = str(uuid.uuid4())
    correct_count = 0
    for att in attempts:
        q = questions_db.get(att.question_id)
        if q and att.selected == q["answer"]:
            correct_count += 1
    total = len(attempts)
    wrong = total - correct_count
    acc = round(correct_count / total * 100, 1) if total else 0
    total_time = sum(a.time_taken for a in attempts)
    return SessionResult(
        session_id=session_id, total=total, correct=correct_count,
        wrong=wrong, accuracy=acc, time_taken=total_time
    )

# ── Notes ─────────────────────────────────────────────────────────────────────
@app.get("/notes", response_model=List[NoteOut], tags=["Notes"])
async def get_notes(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    return [NoteOut(**n) for n in notes_db.values() if n["user_id"] == uid]

@app.post("/notes", response_model=NoteOut, tags=["Notes"])
async def create_note(note: NoteCreate, current_user: dict = Depends(get_current_user)):
    note_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    data = {
        "id": note_id, "user_id": current_user["id"],
        "title": note.title, "body": note.body,
        "subject": note.subject, "chapter": note.chapter,
        "tags": note.tags or [], "created_at": now, "updated_at": now
    }
    notes_db[note_id] = data
    return NoteOut(**data)

@app.put("/notes/{note_id}", response_model=NoteOut, tags=["Notes"])
async def update_note(note_id: str, note: NoteCreate, current_user: dict = Depends(get_current_user)):
    existing = notes_db.get(note_id)
    if not existing or existing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Note not found")
    existing.update({
        "title": note.title, "body": note.body,
        "subject": note.subject, "chapter": note.chapter,
        "tags": note.tags or [], "updated_at": datetime.utcnow().isoformat()
    })
    return NoteOut(**existing)

@app.delete("/notes/{note_id}", tags=["Notes"])
async def delete_note(note_id: str, current_user: dict = Depends(get_current_user)):
    existing = notes_db.get(note_id)
    if not existing or existing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Note not found")
    del notes_db[note_id]
    return {"deleted": True}

# ── Leaderboard ───────────────────────────────────────────────────────────────
@app.get("/leaderboard", tags=["Leaderboard"])
async def get_leaderboard(limit: int = 50):
    sorted_users = sorted(
        [u for u in users_db.values()],
        key=lambda u: u.get("total_questions", 0) * u.get("accuracy", 0),
        reverse=True
    )
    return [
        {"rank": i+1, "name": f"{u['first_name']} {u['last_name']}",
         "score": round(u.get("total_questions", 0) * u.get("accuracy", 0)),
         "accuracy": u.get("accuracy", 0),
         "total_questions": u.get("total_questions", 0)}
        for i, u in enumerate(sorted_users[:limit])
    ]

# ── User Analytics ────────────────────────────────────────────────────────────
@app.get("/analytics/me", tags=["Analytics"])
async def my_analytics(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    user_attempts = [a for a in attempts_db if a["user_id"] == uid]
    # Group by subject
    subject_stats = {}
    for att in user_attempts:
        q = questions_db.get(att["question_id"])
        if q:
            subj = q["subject"]
            if subj not in subject_stats:
                subject_stats[subj] = {"total": 0, "correct": 0}
            subject_stats[subj]["total"] += 1
            if att["correct"]:
                subject_stats[subj]["correct"] += 1
    subject_accuracy = {
        subj: round(d["correct"] / d["total"] * 100, 1) if d["total"] else 0
        for subj, d in subject_stats.items()
    }
    return {
        "total_attempts": len(user_attempts),
        "overall_accuracy": current_user.get("accuracy", 0),
        "streak": current_user.get("streak", 0),
        "subject_accuracy": subject_accuracy,
        "rank": current_user.get("rank"),
    }

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}
