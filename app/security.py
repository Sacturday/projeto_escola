from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os

from jose import JWTError, jwt
from passlib.context import CryptContext

APP_ENV = os.getenv("APP_ENV", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY")
if APP_ENV == "production" and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY é obrigatória em produção")
SECRET_KEY = SECRET_KEY or "desenvolvimento-apenas-troque-esta-chave"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def criar_access_token(dados: dict, expira_em: timedelta | None = None) -> str:
    to_encode = dados.copy()
    expira = datetime.now(timezone.utc) + (expira_em or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expira})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
