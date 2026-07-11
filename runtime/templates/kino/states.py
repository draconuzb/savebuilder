"""Kino shablon FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class AddKino(StatesGroup):
    waiting_code = State()
    waiting_video = State()


class DelKino(StatesGroup):
    waiting_code = State()


class ForceSub(StatesGroup):
    waiting_channel = State()


class Broadcast(StatesGroup):
    waiting_message = State()
    confirming = State()
