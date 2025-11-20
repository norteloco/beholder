from aiogram import Bot, Router, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import modules.keyboards as kb
from modules.states import MenuStates
from modules.providers import Provider
from modules.db.requests import add_chat, add_tracking, del_tracking, get_chat_trackings
from modules.logger import init_logger

router = Router()

logger = init_logger(__name__)


# start
@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Launching the bot and registering the chat in the database.
    """
    await add_chat(message.chat.id)
    logger.info(f"Bot started with chat: {message.chat.id}")
    await message.answer(
        f"""
👋 Hi! I'm a bot that will notify you about new releases in the repositories.
More information is available in the ❔ Help menu or by typing /help.
        """,
        reply_markup=await kb.menu_main(),
    )


# repos
@router.message(Command("repos"))
@router.message(F.text == "📃 Repositories")
async def command_repos_handler(message: Message, state: FSMContext) -> None:
    """
    Opening the repository interaction menu.
        - Adding a repository for tracking
        - Removing a repository from tracking
        - Viewing the list
    """
    await message.answer(
        "What do you want to do with repositories?", reply_markup=await kb.menu_repos()
    )


# help
@router.message(Command("help"))
@router.message(F.text == "❔ Help")
async def command_help_handler(message: Message):
    await message.answer(
        f"""
{html.bold('Repo Watchtower')} is a bot for tracking releases in repositories.

The following providers are currently supported:
    - {html.italic('GitHub')}
    - {html.italic('GitLab')}
    - {html.italic('Docker Hub')}
    
To control the bot, use the menu or commands.

{html.bold('Команды')}:
/start — launch the bot
/menu — return to menu
/repos — go to the repository actions menu
/list — view the list of monitored repositories
/add — add a repository to monitor
/del — remove a repository from monitored lists
/help — view help
/about — information about the bot
        """,
        reply_markup=await kb.menu_main(),
    )


## about
@router.message(Command("about"))
@router.message(F.text == "ℹ️ About")
async def command_about_handler(message: Message):
    await message.answer(
        f"""
Information about the bot.

- Version: 0.1.0
- Author: @norteloco

        """,
        reply_markup=await kb.menu_main(),
    )


# add repisytory tracking
@router.message(Command("add"))
@router.message(F.text == "➕ Add Repository")
async def command_repo_add_handler(message: Message, state: FSMContext):
    await state.set_state(MenuStates.track_add)
    await message.answer(
        f'Please provide a link to your {html.bold("GitHub")}, {html.bold("GitLab")} or {html.bold("Docker Hub")} repository.',
        reply_markup=await kb.menu_return(),
    )


@router.message(MenuStates.track_add)
async def state_repo_add_handler(message: Message, state: FSMContext):
    data = await state.update_data(msg=message.text)
    msg = data["msg"].strip()
    if msg == "🔙 Return":
        await state.set_state(MenuStates.repos_menu)
        await message.answer(
            "What do you want to do with repositories?",
            reply_markup=await kb.menu_repos(),
        )
        return

    provider, namespace, repository, fullname, url = Provider.repository_detect(msg)
    if provider and fullname:
        await add_tracking(
            message.chat.id, provider, namespace, repository, fullname, url
        )
        await message.answer(
            f"✅ Subscription added!\n{provider}: {fullname}",
            reply_markup=await kb.menu_return(),
        )
    else:
        await message.answer(
            f"❌ The source could not be determined. Please check that the URL you entered is correct and try again.",
            reply_markup=await kb.menu_repos(),
        )


## del
@router.message(Command("del"))
@router.message(F.text == "➖ Remove Repository")
async def command_repo_del_handler(message: Message, state: FSMContext):
    await state.set_state(MenuStates.track_del)

    trackings = await get_chat_trackings(message.chat.id)
    list = await kb.menu_repos_list(trackings, "delete")

    if list is None:
        await message.answer("📖 The list of tracked repositories is currently empty.")
        await state.clear()
        return

    await message.answer(
        "⛔️ Select the repository you want to delete from the list:",
        reply_markup=list,
    )
    await message.answer(
        "Press 🔙 Return to cancel", reply_markup=await kb.menu_return()
    )


@router.message(MenuStates.track_del)
async def repo_del_state_handler(message: Message, state: FSMContext):
    data = await state.update_data(msg=message.text)
    msg = data["msg"].strip()
    if msg == "🔙 Return":
        await state.set_state(MenuStates.repos_menu)
        await message.answer(
            "What do you want to do?", reply_markup=await kb.menu_repos()
        )
        return


@router.callback_query(F.data.startswith("delete_"))
async def repo_del_callback_handler(callback: CallbackQuery):
    track_id = int(callback.data.split("_")[1])
    await del_tracking(track_id)
    await callback.answer("✅ Deleted")

    trackings = trackings = await get_chat_trackings(callback.message.chat.id)
    list = await kb.menu_repos_list(trackings, "delete")
    if list is None:
        await callback.message.edit_text(
            "📖 The list of tracked repositories is currently empty.",
            reply_markup=await kb.menu_repos(),
        )
        return
    await callback.message.edit_text(
        text="⛔️ Select the repository you want to delete from the list:",
        reply_markup=list,
    )


# list of tracked repos
@router.message(Command("list"))
@router.message(F.text == "📋 List of Repositories")
async def command_repo_list_handler(message: Message, state: FSMContext):
    trackings = await get_chat_trackings(message.chat.id)
    list = await kb.menu_repos_list(trackings, "view")

    if list is None:
        await message.answer("📖 The list of tracked repositories is currently empty.")
        return

    await message.answer(
        "📋 List of tracked repositories:",
        reply_markup=list,
    )
    await message.answer(f"What do you want to do?", reply_markup=await kb.menu_repos())


# menu
@router.message(Command("menu"))
@router.message(F.text == "🏠 Menu")
async def command_menu_handler(message: Message):
    await message.answer("🏠 Return to menu", reply_markup=await kb.menu_main())
