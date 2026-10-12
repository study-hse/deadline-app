"""Deadline Tracker: маленький сервис для учебных дедлайнов."""

from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

VERSION = "1.0.0"

app = FastAPI(title="Deadline Tracker", version=VERSION)

# Данные хранятся в памяти: при перезапуске сервиса список очищается.
deadlines = []
counter = {"next_id": 1}


class DeadlineIn(BaseModel):
    title: str
    subject: str
    due_date: date


@app.get("/")
def root():
    return {"message": "Deadline Tracker: сервис учебных дедлайнов"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": VERSION}


@app.get("/deadlines")
def list_deadlines(subject: str | None = None):
    if subject is None:
        return deadlines
    return [d for d in deadlines if d["subject"] == subject]


@app.get("/deadlines/{deadline_id}")
def get_deadline(deadline_id: int):
    for d in deadlines:
        if d["id"] == deadline_id:
            return d
    raise HTTPException(status_code=404, detail="Задание не найдено")


@app.post("/deadlines", status_code=201)
def create_deadline(data: DeadlineIn):
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Название не может быть пустым")
    if data.due_date < date.today():
        raise HTTPException(status_code=400, detail="Срок не может быть в прошлом")
    item = {
        "id": counter["next_id"],
        "title": data.title,
        "subject": data.subject,
        "due_date": data.due_date.isoformat(),
        "done": False,
    }
    counter["next_id"] += 1
    deadlines.append(item)
    return item


@app.post("/deadlines/{deadline_id}/done")
def mark_done(deadline_id: int):
    for d in deadlines:
        if d["id"] == deadline_id:
            d["done"] = True
            return d
    raise HTTPException(status_code=404, detail="Задание не найдено")
