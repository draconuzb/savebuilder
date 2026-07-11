"""Media-kod shablonlari uchun spetsifikatsiya (kino/audio umumiy pattern)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaSpec:
    media_type: str  # video / audio
    emoji: str
    noun: str  # "Kino" / "Audio"
    ask_word: str  # "video" / "audio"


KINO = MediaSpec(media_type="video", emoji="🎬", noun="Kino", ask_word="video")
AUDIO = MediaSpec(media_type="audio", emoji="🎵", noun="Audio", ask_word="audio")
SERIAL = MediaSpec(media_type="video", emoji="🎞", noun="Serial", ask_word="video")
