from typing import Callable, Any, Coroutine
import string


class Commands:
    """
    Normalizes string coming from TTS. Runs function and returns result or True if
    it ran successfully. Returns None if key not found, False if found and exception raised.
    """

    def __init__(self, data: dict[str, Coroutine]):
        """Dictionary of functions to be executed at index."""
        self.data = data
        self.no_punctuation = str.maketrans("", "", string.punctuation)

    def __repr__(self):
        return ", ".join(list(self.data.keys()))

    def __getitem__(self, key: str) -> Callable:
        return self.data[key]

    def __setitem__(self, key: str, value: Callable):
        self.data[key] = value

    async def execute(self, key: str) -> Any | bool | None:
        key = key.lower().translate(self.no_punctuation)
        func = self.data.get(key)
        if func is None:
            return None
        try:
            result = await func()
        except BaseException as e:
            print(f"Failed to execute command '{key}'.", e)
            return False
        return True if result is None else result
