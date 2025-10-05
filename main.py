from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import uuid

# --- База данных ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String)
    bio = Column(String, default="")
    goal = Column(String, default="")  # chat, relationship, sex, hobby
    height = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    interests = Column(String, default="")  # через запятую: "кино,спорт"
    photo_url = Column(String, default="")
    is_premium = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Отдаём главную страницу ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Отдаём экран профиля ---
@app.get("/profile", response_class=HTMLResponse)
def profile_page():
    html_path = os.path.join(os.path.dirname(__file__), "profile.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Получаем данные пользователя ---
@app.get("/api/user/{tg_id}")
def get_user(tg_id: int):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.tg_id == tg_id).first()
    db.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "tg_id": user.tg_id,
        "username": user.username,
        "first_name": user.first_name,
        "bio": user.bio,
        "goal": user.goal,
        "height": user.height,
        "weight": user.weight,
        "interests": user.interests.split(",") if user.interests else [],
        "photo_url": user.photo_url
    }

# --- Сохраняем профиль ---
class ProfileUpdate(BaseModel):
    tg_id: int
    bio: str = ""
    goal: str = ""
    height: int = None
    weight: int = None
    interests: list = []

@app.post("/api/profile")
def update_profile(data: ProfileUpdate):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.tg_id == data.tg_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    user.bio = data.bio
    user.goal = data.goal
    user.height = data.height
    user.weight = data.weight
    user.interests = ",".join(data.interests)
    
    db.commit()
    db.close()
    return {"status": "ok"}

# --- Регистрация (без изменений) ---
class UserRequest(BaseModel):
    tg_id: int
    username: str = None
    first_name: str

@app.post("/register")
def register(user: UserRequest):
    db = SessionLocal()
    db_user = db.query(UserDB).filter(UserDB.tg_id == user.tg_id).first()
    if db_user:
        db_user.username = user.username
        db_user.first_name = user.first_name
    else:
        db_user = UserDB(
            tg_id=user.tg_id,
            username=user.username,
            first_name=user.first_name
        )
        db.add(db_user)
    db.commit()
    db.close()
    return {"status": "ok"}
