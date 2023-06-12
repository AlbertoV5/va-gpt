from openai import ChatCompletion
from typing import Generator
import re


class Streamer:
    """Chat completion stream"""

    def __init__(self) -> None:
        pass

    def reader(
        self, generator: Generator[dict, None, None]
    ) -> Generator[tuple[str, int], None, None]:
        """
        Reads tokens in a sequence until it finds a new line, then
        yields the line with the token count.
        """
        NEW_LINE = "\n\n"
        line = ""
        token = ""
        token_count = 0
        for event in generator:
            delta = event["choices"][0]["delta"]
            if "content" in delta:
                token = delta["content"]
                line += token
                token_count += 1
            if not delta or NEW_LINE in line:
                yield line, token_count
                line = ""
                token_count = 0

    def request(self, request: dict, min_block_size=40):
        """Request Completion stream and return blocks of text or code.
        https://platform.openai.com/docs/api-reference/chat/create
        """
        NEW_CODE = "```"
        current_block_is_code = False
        block_size = 0
        block = []
        # flow
        for line, count in self.reader(ChatCompletion.create(**request)):
            # detect code blocks
            if NEW_CODE in line:
                if len(re.findall(NEW_CODE, line)) == 2:
                    # if it is a one-line code, yield text, and then code
                    yield "".join(block), block_size
                    yield line, count
                    block = []
                    block_size = 0
                    continue
                current_block_is_code = not current_block_is_code
                if current_block_is_code:
                    # if it is a code block, yield the previous block
                    yield "".join(block), block_size
                    block = [line]
                    block_size = count
                else:
                    # if it is the end of a code block, write, then yield the block
                    block.append(line)
                    yield "".join(block), block_size
                    block = []
                    block_size = 0
            else:
                block.append(line)
                block_size += count
            # yields block if it has enough tokens or keys are empty
            if block_size >= min_block_size and not current_block_is_code:
                yield "".join(block), block_size
                block = []
                block_size = 0
        # yield the rest
        if block_size > 0:
            yield "".join(block), block_size
