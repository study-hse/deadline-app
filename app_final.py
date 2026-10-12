"""Deadline Tracker: маленький сервис для учебных дедлайнов."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

VERSION = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("deadline_tracker")


@asynccontextmanager
async def lifespan(_app):
    logger.info("Сервис запущен, WARN_DAYS=%s", get_warn_days())
    yield


app = FastAPI(title="Deadline Tracker", version=VERSION, lifespan=lifespan)

# Данные хранятся в памяти: при перезапуске сервиса список очищается.
deadlines = []
counter = {"next_id": 1}


class DeadlineIn(BaseModel):
    title: str
    subject: str
    due_date: date


def get_warn_days() -> int:
    """Сколько дней считается «горящим» сроком (из переменной окружения)."""
    return int(os.getenv("WARN_DAYS", "3"))


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


# Этот маршрут должен идти ДО /deadlines/{deadline_id},
# иначе слово "upcoming" будет принято за номер задания.
@app.get("/deadlines/upcoming")
def upcoming(days: int | None = None):
    if days is None:
        days = get_warn_days()
    today = date.today()
    limit = today + timedelta(days=days)
    result = []
    for d in deadlines:
        due = date.fromisoformat(d["due_date"])
        if not d["done"] and today <= due <= limit:
            result.append({**d, "days_left": (due - today).days})
    result.sort(key=lambda item: item["due_date"])
    logger.info("Запрос ближайших дедлайнов на %s дн.: найдено %s", days, len(result))
    return result


@app.get("/deadlines/{deadline_id}")
def get_deadline(deadline_id: int):
    for d in deadlines:
        if d["id"] == deadline_id:
            return d
    logger.warning("Запрошено несуществующее задание %s", deadline_id)
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
    logger.info("Добавлено задание %s: %s", item["id"], item["title"])
    return item


@app.post("/deadlines/{deadline_id}/done")
def mark_done(deadline_id: int):
    for d in deadlines:
        if d["id"] == deadline_id:
            d["done"] = True
            logger.info("Задание %s отмечено выполненным", deadline_id)
            return d
    logger.warning("Попытка отметить несуществующее задание %s", deadline_id)
    raise HTTPException(status_code=404, detail="Задание не найдено")
