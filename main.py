from src.engine.prelude import *
import string

from src.world import World
from src.assets import Assets
from src.consts import *

class App(SceneManager):
    def __init__(self):
        camera.init_window(WIDTH, HEIGHT, TITLE, FPS, PROJ_SIZE, 0)
        ctx.load_shaders("assets/shaders", LIT_SHADER, UNLIT_SHADER, UI_SHADER, REPLACE_SHADER)
        #font.add_font("main", pygame.Font("assets/pixelated.tff", 50), string.ascii_letters+string.digits+string.punctuation+" ", False)
        scriptable.load("assets/scriptables")
        self.assets = Assets()
        self.load_scene(World.name, MapData.get("map0"))

if __name__ == "__main__":
    App().run()
