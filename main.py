from src.engine.prelude import *
import asyncio
if not USE_ZEN:
    # hidden import for PyInstaller
    import glcontext
print("PORCODIO")
from src.world import World
from src.main_menu import MainMenu
from src.assets import Assets
from src.sounds import Sounds
from src.settings import Settings, Languages
from src.consts import *
from src import god 

class App(SceneManager):
    def __init__(self):
        god.app = self 
        Sounds.pre_init()
        Settings.get_user_path()
        camera.init_window(WIDTH, HEIGHT, TITLE, PROJ_SIZE, 0, pygame.image.load("assets/images/enemies/boss_bot.png"))
        ctx.load_shaders("assets/shaders", LIT_SHADER, UNLIT_SHADER, UI_SHADER, REPLACE_SHADER)
        scriptable.load("assets/scriptables")
        
        god.lang = Languages()
        god.settings = Settings()  
        god.assets = Assets()
        god.assets.finish_load()
        
        god.sounds = Sounds()   
        
        #self.load_scene(World.name, MapData.get("map0"))
        self.load_scene(MainMenu.name)
        #import ez_profile

    def pre_render(self):
        camera.upload_uniforms(LIT_SHADER, UNLIT_SHADER, REPLACE_SHADER)
        camera.upload_ui_uniforms(UI_SHADER)
        texture.upload_samplers(MAX_SAMPLERS, TEXTURES_UNIFORM, LIT_SHADER, UNLIT_SHADER, REPLACE_SHADER, UI_SHADER)
        god.assets.use()

    def post_render(self):
        camera.tick_window(god.settings.fps)
        
    def on_quit(self):
        god.settings.save()

if __name__ == "__main__":
    app = App()
    asyncio.run(app.run())
