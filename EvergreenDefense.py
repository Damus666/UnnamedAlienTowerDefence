from src.engine.prelude import *
# hidden import for PyInstaller
import glcontext

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
        self.screen_buffer = Screenbuffer()
        self.screen_buffer.refresh_buffer(WIDTH, HEIGHT, god.settings.scaled_mul)
        
        #self.load_scene(World.name, MapData.get("map0"))
        self.load_scene(MainMenu.name)
        #import ez_profile

    def pre_render(self):
        camera.upload_uniforms(LIT_SHADER, UNLIT_SHADER, REPLACE_SHADER)
        camera.upload_ui_uniforms(UI_SHADER)
        texture.upload_samplers(MAX_SAMPLERS, TEXTURES_UNIFORM, LIT_SHADER, UNLIT_SHADER, REPLACE_SHADER, UI_SHADER)
        god.assets.use()
        if god.settings.scaled_mul != 1:
            self.screen_buffer.pre_render()

    def post_render(self):
        if not god.settings.ui_high_res and god.settings.scaled_mul != 1:
            god.app.screen_buffer.post_render()
        camera.tick_window(god.settings.fps)
        
    def on_quit(self):
        god.settings.save()
        self.screen_buffer.free()

if __name__ == "__main__":
    App().run()
