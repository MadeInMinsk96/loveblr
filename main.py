from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    tg_id: int
    username: str = None
    first_name: str

@app.post("/register")
def register(user: User):
    # Здесь позже будет сохранение в базу
    return {"status": "ok", "message": f"Привет, {user.first_name}!"}

@app.get("/")
def home():
    return {"app": "SoulMatch Backend is running!"}