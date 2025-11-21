from aiogram.fsm.state import StatesGroup, State


class MenuStates(StatesGroup):
    repos_menu = State()  # 📃 Repositories
    track_add = State()  # ➕ Add Repository
    track_del = State()  # ➖ Remove Repository
