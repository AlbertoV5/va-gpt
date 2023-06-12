"""
Chat Context
"""
from pydantic import BaseModel, Field
import yaml


class UserContext(BaseModel):
    title: str = Field(max_length=32)
    name: str = Field(max_length=32)
    context_: "Context" = None


class LogitBias(BaseModel):
    text: str
    bias: int


class AssistantContext(UserContext):
    logit_bias_: list[LogitBias] = Field(alias="logit_bias")

    @property
    def logit_bias(self):
        return {item.text.format(context=self.context_): item.bias for item in self.logit_bias_}


class SystemContext(BaseModel):
    message_: str = Field(alias="message")
    context_header_: str | None = Field(alias="context_header")
    context_: "Context" = None

    @property
    def message(self):
        """Returns the system message content with formatted messages content."""
        return self.message_.format(context=self.context_) if self.message_ else ""

    @property
    def context_header(self):
        return self.context_header_.format(context=self.context_) if self.context_header_ else ""


class Context(BaseModel):
    user_: UserContext = Field(alias="user")
    assistant_: AssistantContext = Field(alias="assistant")
    system_: SystemContext = Field(alias="system")
    context_file: str = ""

    @classmethod
    def from_yaml(cls, filename: str):
        """Load context from YAML file."""
        with open(filename, "rb") as f:
            c = Context(**yaml.safe_load(f))
        c.context_file = filename
        return c

    def update(self):
        """Reload YAML file from"""
        try:
            c = Context.from_yaml(self.context_file)
            self.user_ = c.user_
            self.assistant_ = c.assistant_
            self.system_ = c.system_
        except BaseException as e:
            print(e)

    @property
    def system(self):
        """Update the system's Context (self) reference, then return it."""
        self.system_.context_ = self
        return self.system_

    @property
    def user(self):
        self.user_.context_ = self
        return self.user_

    @property
    def assistant(self):
        self.assistant_.context_ = self
        return self.assistant_
