from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
from aiogram.fsm.context import FSMContext

from modules.states import MenuStates
from modules.db.requests import get_chat_trackings


# main
async def menu_main() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📃 Repositories")],
            [KeyboardButton(text="❔ Help")],
            [KeyboardButton(text="ℹ️ About")],
        ],
        resize_keyboard=True,
    )
    return kb


# repositories
async def menu_repos() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Add Repository"),
                KeyboardButton(text="➖ Remove Repository"),
            ],
            [
                KeyboardButton(text="📋 List of Repositories"),
            ],
            [
                KeyboardButton(text="🏠 Menu"),
            ],
        ],
        resize_keyboard=True,
    )
    return kb


# return button keyboard
async def menu_return() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔙 Return"),
            ]
        ],
        resize_keyboard=True,
    )
    return kb


# trackings list inline keyboard with modes
async def menu_repos_list(trackings, mode: str = "view") -> InlineKeyboardMarkup | None:
    if not trackings:
        return None

    kb = InlineKeyboardBuilder()
    for item in trackings:
        if mode == "delete":
            text = f"❌ {item.provider}: {item.namespace}/{item.repository}"
            kb.button(
                text=text,
                callback_data=f"delete_{item.id}",
            )
        else:
            text = f"{item.provider}: {item.namespace}/{item.repository}"
            kb.button(
                text=text,
                url=item.url,
                callback_data=f"view_{item.id}",
            )
    return kb.adjust(1).as_markup()  # type: ignore
