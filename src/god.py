import typing
if typing.TYPE_CHECKING:
    from ..EvergreenDefense import App
    from .world import World
    from .assets import Assets
    from .settings import Settings, Languages
    from .sounds import Sounds
    from .player import Player

app: "App" = None
assets: "Assets" = None
settings: "Settings" = None
world: "World" = None
player: "Player" = None
lang: "Languages" = None
sounds: "Sounds" = None
