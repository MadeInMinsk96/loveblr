from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
import requests
import os
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random

# --- Настройки ---
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "819c3afe10daa867a50816100412c7bd")  # замени на свой!
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# --- База данных ---
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
    goal = Column(String, default="")
    height = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    interests = Column(String, default="")
    photo_url = Column(String, default="")
    is_premium = Column(Boolean, default=False)

class LikeDB(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, index=True)
    to_user_id = Column(Integer, index=True)
    is_mutual = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Страницы ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/profile", response_class=HTMLResponse)
def profile_page():
    with open(os.path.join(os.path.dirname(__file__), "profile.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/search", response_class=HTMLResponse)
def search_page():
    with open(os.path.join(os.path.dirname(__file__), "search.html"), "r", encoding="utf-8") as f:
        return f.read()

# --- API ---
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
        db_user = UserDB(tg_id=user.tg_id, username=user.username, first_name=user.first_name)
        db.add(db_user)
    db.commit()
    db.close()
    return {"status": "ok"}

class ProfileUpdate(BaseModel):
    tg_id: int
    bio: str = ""
    goal: str = ""
    height: int = None
    weight: int = None
    interests: list = []

@app.post("/api/profile")
def update_profile( ProfileUpdate):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.tg_id == data.tg_id).first()
    if not user:
        raise HTTPException(404)
    user.bio = data.bio
    user.goal = data.goal
    user.height = data.height
    user.weight = data.weight
    user.interests = ",".join(data.interests)
    db.commit()
    db.close()
    return {"status": "ok"}

# --- НОВОЕ: Загрузка фото ---
@app.post("/api/upload-photo")
async def upload_photo(tg_id: int, file: UploadFile = File(...)):
    # Сохраняем файл временно
    contents = await file.read()
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(contents)

    # Отправляем в ImgBB
    with open(temp_path, "rb") as f:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY},
            files={"image": f}
        )
    
    os.remove(temp_path)
    if response.status_code != 200:
        raise HTTPException(500, "Не удалось загрузить фото")
    
    photo_url = response.json()["data"]["url"]

    # Сохраняем в базу
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.tg_id == tg_id).first()
    if user:
        user.photo_url = photo_url
        db.commit()
    db.close()
    return {"photo_url": photo_url}

@app.get("/api/user/{tg_id}")
def get_user(tg_id: int):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.tg_id == tg_id).first()
    db.close()
    if not user:
        raise HTTPException(404)
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

@app.get("/api/search")
def search_users(current_user_id: int):
    db = SessionLocal()
    liked_ids = db.query(LikeDB.to_user_id).filter(LikeDB.from_user_id == current_user_id).all()
    liked_ids = [x[0] for x in liked_ids]
    liked_ids.append(current_user_id)

    users = db.query(UserDB).filter(
        and_(
            UserDB.tg_id.notin_(liked_ids),
            UserDB.tg_id != current_user_id
        )
    ).all()

    if not users:
        return {"user": None}

    random_user = random.choice(users)
    db.close()
    return {
        "user": {
            "tg_id": random_user.tg_id,
            "first_name": random_user.first_name,
            "bio": random_user.bio,
            "goal": random_user.goal,
            "height": random_user.height,
            "weight": random_user.weight,
            "interests": random_user.interests.split(",") if random_user.interests else [],
            "username": random_user.username,
            "photo_url": random_user.photo_url
        }
    }

class LikeRequest(BaseModel):
    from_user_id: int
    to_user_id: int

@app.post("/api/like")
def like_user( LikeRequest):
    db = SessionLocal()
    existing = db.query(LikeDB).filter(
        LikeDB.from_user_id == data.from_user_id,
        LikeDB.to_user_id == data.to_user_id
    ).first()
    if existing:
        db.close()
        return {"status": "already_liked"}

    new_like = LikeDB(from_user_id=data.from_user_id, to_user_id=data.to_user_id)
    db.add(new_like)

    mutual = db.query(LikeDB).filter(
        LikeDB.from_user_id == data.to_user_id,
        LikeDB.to_user_id == data.from_user_id
    ).first()

    is_match = False
    if mutual:
        new_like.is_mutual = True
        mutual.is_mutual = True
        is_match = True

    db.commit()
    db.close()
    return {"status": "ok", "is_match": is_match}
