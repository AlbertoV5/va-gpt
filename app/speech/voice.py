"""
SSML Voice Customization
"""
from xml.etree.ElementTree import parse, tostring, register_namespace

ns, value = "amazon", "amazon"
register_namespace(ns, value)


class VoiceStyle:
    ssml: str
    """SSML String for styling speech."""

    def __init__(self, filepath: str, default="<speak>{text}</speak>") -> None:
        self.filepath = filepath
        self.default_ssml = default
        self.language = ""
        self.voice_id = ""
        self.engine = ""
        # ssml
        self.ssml = ""
        self.update()

    def select(self, name: str):
        """Select style by name."""
        style = self.root.find(f"./style[@name='{name}']")
        speak = style.find("speak") if style else None
        self.ssml = (
            tostring(speak, encoding="unicode").replace(f' xmlns:{ns}="{value}"', "", 1)
            if speak
            else self.default_ssml
        )

    def update(self):
        """Reload XML file."""
        try:
            with open(self.filepath, "rb") as file:
                self.root = parse(file).getroot()
            # config
            self.language = self.root.get("language", default="en-US")
            self.voice_id = self.root.get("voice", default="Salli")
            self.engine = self.root.get("engine", default="standard")
            # ssml style
            name = self.root.get("style", default="base")
            self.select(name)
        except BaseException as e:
            print(e)

    @classmethod
    def from_xml(cls, filepath: str):
        """Load Voice Styles from XML file."""
        return VoiceStyle(filepath=filepath)
