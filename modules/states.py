from aiogram.fsm.state import StatesGroup, State


class MenuStates(StatesGroup):
    main_menu = State()  # Main /start
    repos_menu = State()  # 📃 Repositories
    track_add = State()  # ➕ Add Repository
    track_del = State()  # ➖ Remove Repository
    track_list = State()  # 📋 List of Repositories
