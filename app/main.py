import os
import time

import psycopg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from psycopg.rows import dict_row
from pydantic import BaseModel, field_validator

app = FastAPI(title="team-notes-api")


def get_conn():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        row_factory=dict_row,
    )


def init_db(retries: int = 10):
    # La BD puede tardar unos segundos en arrancar, por eso se reintenta
    for _ in range(retries):
        try:
            with get_conn() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(150) NOT NULL,
                        content TEXT NOT NULL,
                        author VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )
            return
        except psycopg.OperationalError:
            time.sleep(2)
    raise RuntimeError("No se pudo conectar a la base de datos")


@app.on_event("startup")
def startup():
    init_db()


# ---------- Modelo y validaciones ----------
class NoteIn(BaseModel):
    title: str
    content: str
    author: str

    @field_validator("title", "content", "author")
    @classmethod
    def not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("no puede estar vacío")
        return value.strip()


def serialize(note: dict) -> dict:
    note["created_at"] = note["created_at"].isoformat()
    return note


# ---------- Manejo de errores ----------
@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    campos = [str(e["loc"][-1]) for e in exc.errors()]
    return JSONResponse(
        status_code=400,
        content={"error": "Datos inválidos", "fields": sorted(set(campos))},
    )


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    # No se exponen detalles internos al cliente
    return JSONResponse(status_code=500, content={"error": "Error interno del servidor"})


def not_found():
    return JSONResponse(status_code=404, content={"error": "Nota no encontrada"})


# ---------- Lectura (Estudiante A) ----------
@app.get("/health")
def health():
    return {"status": "ok", "environment": os.getenv("APP_ENV", "development")}


@app.get("/notes")
def list_notes():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM notes ORDER BY id").fetchall()
    return [serialize(r) for r in rows]


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = %s", (note_id,)).fetchone()
    if row is None:
        return not_found()
    return serialize(row)
