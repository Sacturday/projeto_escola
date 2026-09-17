from __future__ import annotations
import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Sao_Paulo")
TZ = ZoneInfo(APP_TIMEZONE)

def agora_rede() -> datetime:
    return datetime.now(timezone.utc).astimezone(TZ)

def hoje_rede() -> date:
    return agora_rede().date()
