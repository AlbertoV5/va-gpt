from app.assistant import Assistant
from app.broadcast import Broadcast
from app.audio import AudioChannel
from app.storage import Storage

from datetime import datetime, timedelta
import pyperclip

# systems
storage = Storage()
broadcast = Broadcast()
channel = AudioChannel()
# assistant
assistant = Assistant()
assistant.storage = storage
assistant.channel = channel
assistant.broadcast = broadcast


async def show_commands():
    return assistant.commands


async def show_system_message():
    return assistant.chat.system_message()


async def show_short_term_memory():
    return assistant.chat.short_term


async def show_long_term_memory():
    return assistant.chat.long_term


async def clear_short_term_memory():
    assistant.chat.short_term = None
    return assistant.chat.short_term


async def update_context():
    assistant.context.update()
    return assistant.context


async def update_voice():
    assistant.voice.update()
    return assistant.voice


async def copy_clipboard_as_code():
    """Copy clipboard contents into assistant's notes."""
    assistant.notes = f"```\n{pyperclip.paste()}\n```"
    return broadcast.to_markdown(assistant.notes)


async def copy_clipboard_as_text():
    """Copy clipboard contents into assistant's notes."""
    assistant.notes = f"\n{pyperclip.paste()}"
    return broadcast.to_markdown(assistant.notes)


async def generate_reaper_project(today=datetime.now(), days=1):
    """Generate RPP file from given dates."""
    sources = await storage.db.read_from_dates(today - timedelta(days=days), today)
    filepath = storage.directory / f"{today.strftime('%Y-%m-%d_%H-%M-%S')}.RPP"
    storage.rpp.create(sources, filepath)
    return filepath


async def exit_program():
    assistant.stop()
    # await database.close()


async def startup():
    """Startup commands"""
    # await load_history()


assistant.commands = {
    "startup": startup,
    "show commands": show_commands,
    "show system message": show_system_message,
    "show long term memory": show_long_term_memory,
    "show short term memory": show_short_term_memory,
    "clear short term memory": clear_short_term_memory,
    "copy clipboard as code": copy_clipboard_as_code,
    "copy clipboard as text": copy_clipboard_as_text,
    "generate reaper project": generate_reaper_project,
    "update context": update_context,
    "update voice": update_voice,
    "exit program": exit_program,
}
