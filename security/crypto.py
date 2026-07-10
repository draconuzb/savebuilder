"""Bola bot tokenlarini shifrlash/deshifrlash (Fernet)."""
from __future__ import annotations

from cryptography.fernet import Fernet

from core.config import get_settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(get_settings().fernet_key.encode())
    return _fernet


def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(enc: str) -> str:
    return _get_fernet().decrypt(enc.encode()).decode()
