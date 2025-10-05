from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# --- Настройка базы данных ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # на Render будет PostgreSQL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Модель пользователя ---
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
    is_premium = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# --- FastAPI ---
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

class UserRequest(BaseModel):
    tg_id: int
    username: str = None
    first_name: str

@app.post("/register")
def register(user: UserRequest):
    db = SessionLocal()
    try:
        # Ищем, есть ли уже такой пользователь
        db_user = db.query(UserDB).filter(UserDB.tg_id == user.tg_id).first()
        if db_user:
            # Обновляем данные (на случай, если изменил username)
            db_user.username = user.username
            db_user.first_name = user.first_name
        else:
            # Создаём нового
            db_user = UserDB(
                tg_id=user.tg_id,
                username=user.username,
                first_name=user.first_name
            )
            db.add(db_user)
        db.commit()
        return {"status": "ok", "message": f"Профиль сохранён, {user.first_name}!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
