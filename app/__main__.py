from typing import Protocol
import argparse
import warnings
import asyncio
import os

from app.system.config import Config
from app.speech import VoiceStyle
from app.chat import Context

from app import channel, storage, broadcast, assistant

# ignore pytorch non-writeable buffer warning
warnings.filterwarnings("ignore")
os.environ["CUDA_VISIBLE_DEVICES"] = ""


class Arguments(Protocol):
    config: str
    context: str
    voice: str


def main(argv: Arguments):
    """
    Main process
    """
    # Run normal process.
    loading_screen = broadcast.startup("Loading...", "GPT-VA")
    for msg in loading_screen:
        # Load config.
        context = Context.from_yaml(argv.context)
        voice = VoiceStyle.from_xml(argv.voice)
        config = Config.from_toml(argv.config)
        broadcast.load(context)
        channel.load(config.audio)
        storage.load(config.storage)
        assistant.load(config, voice, context)
        # Execute startup command.
        asyncio.run(assistant.commands.execute("startup"))
        # Update loading screen.
        loading_screen.send(msg.format(bold="System", text=context.system.message))
    try:
        # Start assistant.
        asyncio.run(assistant.start())
    except KeyboardInterrupt:
        print(f"\nInterrupted by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="A.I. Assistant",
        description="GPT",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Location of config file.",
    )
    parser.add_argument(
        "--context",
        type=str,
        default="context.yml",
        help="Location of context file.",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="cvoice.xml",
        help="Location of voice style file.",
    )
    main(parser.parse_args())
    print("Bye!")
