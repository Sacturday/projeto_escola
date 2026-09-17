from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas
from ..database import get_db
from ..security import criar_access_token, verificar_senha

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
async def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    usuario = (
        await db.execute(
            select(models.Usuario).where(
                models.Usuario.username == form.username,
                models.Usuario.ativo.is_(True),
            )
        )
    ).scalar_one_or_none()

    if not usuario or not verificar_senha(form.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    token = criar_access_token({"sub": usuario.username, "perfil": usuario.perfil.value})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("APP_ENV", "development").lower() == "production",
        max_age=3600,
        path="/",
    )

    destino = {
        models.Perfil.ADMIN: "/admin",
        models.Perfil.DIRETOR: "/diretor",
        models.Perfil.PROFESSOR: "/turmas",
    }[usuario.perfil]
    response.headers["HX-Redirect"] = destino
    return {"access_token": token, "token_type": "bearer"}


@router.get("/logout")
async def logout_pagina(response: Response):
    redirecionamento = RedirectResponse(url="/", status_code=303)
    redirecionamento.delete_cookie("access_token")
    return redirecionamento


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "ok"}
