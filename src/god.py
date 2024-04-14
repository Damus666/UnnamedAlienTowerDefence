import typing
if typing.TYPE_CHECKING:
    from ..main import App
    from .world import World
    from .assets import Assets
    from .settings import Settings, LanguageManager
    from .player import Player

app: "App" = None
assets: "Assets" = None
settings: "Settings" = None
world: "World" = None
player: "Player" = None
lang: "LanguageManager" = None
