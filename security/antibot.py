"""Telegram Mini App initData validatsiyasi (anti-bot xavfsizlik tekshiruvi).

Rasmiy spetsifikatsiya: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_init_data(init_data: str, bot_token: str, max_age: int = 3600) -> dict | None:
    """initData ni tekshiradi. To'g'ri bo'lsa parse qilingan user dict qaytaradi, aks holda None.

    max_age: auth_date dan necha soniya o'tishga ruxsat (replay himoyasi)."""
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    # data_check_string: kalitlar alifbo tartibida, key=value \n bilan
    data_check_string = "\n".join(
        f"{k}={parsed[k]}" for k in sorted(parsed.keys())
    )
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Vaqtni tekshirish (replay himoyasi)
    auth_date = parsed.get("auth_date")
    if auth_date and max_age:
        try:
            if time.time() - int(auth_date) > max_age:
                return None
        except ValueError:
            return None

    # user JSON'ni ajratish
    user_raw = parsed.get("user")
    if not user_raw:
        return None
    try:
        return json.loads(user_raw)
    except json.JSONDecodeError:
        return None
