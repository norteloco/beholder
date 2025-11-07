from aiogram.fsm.state import StatesGroup, State


class MenuStates(StatesGroup):
    repos_menu = State()
    track_add = State()
    track_del = State()
    track_list = State()
