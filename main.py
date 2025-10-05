from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os

app = FastAPI()

# Раздаём статические файлы (HTML, CSS, JS)
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

class User(BaseModel):
    tg_id: int
    username: str = None
    first_name: str

@app.post("/register")
def register(user: User):
    return {"status": "ok", "message": f"Привет, {user.first_name}!"}
