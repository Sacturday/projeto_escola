from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import engine
from .routers import admin, auth, diretor, frequencias, importacoes, paginas, websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="Sistema de Controle de Frequência Escolar", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(paginas.router)
app.include_router(auth.router)
app.include_router(frequencias.router)
app.include_router(websockets.router)
app.include_router(admin.pages)
app.include_router(admin.router)
app.include_router(importacoes.router)
app.include_router(diretor.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
