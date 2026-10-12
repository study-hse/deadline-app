"""Deadline Tracker: маленький сервис для учебных дедлайнов."""

from fastapi import FastAPI

VERSION = "1.0.0"

app = FastAPI(title="Deadline Tracker", version=VERSION)


@app.get("/")
def root():
    return {"message": "Deadline Tracker: сервис учебных дедлайнов"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": VERSION}
