"""Manager bot FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class CreateBot(StatesGroup):
    choosing_category = State()
    choosing_template = State()
    waiting_token = State()
    choosing_tariff = State()
