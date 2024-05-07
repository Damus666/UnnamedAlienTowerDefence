from .engine.prelude import *
import os

from .consts import *
from . import god

class Assets:
    def __init__(self):
        self.font_atlas = SpriteAtlas(20)
        font.add_font(MAIN_FONT, pygame.Font("assets/fonts/alienbig.ttf", 300), 
                      self.font_atlas, FONT_ATLAS, True, FONT_SCALE, "àù€äöüßÄÖÜőáúűóöüúéŐÚíÁ", 
                      "אבגדהוזחטיכךלמםנןסעפףתץקרשת", pygame.Font("assets/fonts/hebrew.ttf", 300),
                      "ج ح خ ه ع غ ف ق ث ص ض ة ك م ن ت ا ل ب ي س ش ى و ر ز د ذ ط ظ ء", pygame.Font("assets/fonts/arabic.ttf", 300))
        self.font_atlas.build("font_atlas")
        self.loading_screen()
        
    def loading_screen(self):
        ctx.clear((0, 0, 0, 1))
        texture.upload_samplers(MAX_SAMPLERS, TEXTURES_UNIFORM, LIT_SHADER, UNLIT_SHADER, REPLACE_SHADER, UI_SHADER)
        camera.upload_ui_uniforms(UI_SHADER)
        self.font_atlas.texture.use(FONT_ATLAS)
        FixedRectsBatch(font.render_single_center(MAIN_FONT, f"{god.lang["loading"]}", (0, 0), 10)).create_vao(UI_SHADER, *SHADER_UNIFORMS).render()
        camera.tick_window(god.settings.fps)
    
    def finish_load(self):
        self.player = self.load_player()
        
        self.world_atlas = SpriteAtlas()
        self.ui_atlas = SpriteAtlas(2)
        
        self.load_folders("tiles", "trees", "buildings", "other", "particles", "enemies", "items")
        self.load_ui_folders("items", "trees", "buildings", "icons")
        self.load_named_folders("plants", "stars")
        self.load_pg()
        
        self.world_atlas.build("world_atlas")
        self.ui_atlas.build("ui_atlas")
        
        
    def get_uvs(self, name, folder_name=None, flipx=False):
        return self.world_atlas.get_uvs(name if folder_name is None else f"{folder_name}/{name}", flipx)
        
        
    def get_ui_uvs(self, name, folder_name=None, flipx=False):
        return self.ui_atlas.get_uvs(name if folder_name is None else f"{folder_name}/{name}", flipx)
        
    def use(self):
        self.world_atlas.texture.use(WORLD_ATLAS)
        self.ui_atlas.texture.use(UI_ATLAS)
        self.font_atlas.texture.use(FONT_ATLAS)
                
    def load_pg(self):
        circle, circle_o, square = (pygame.Surface((CIRCLE_RADIUS*2, CIRCLE_RADIUS*2), pygame.SRCALPHA), 
                                    pygame.Surface((CIRCLE_RADIUS*2, CIRCLE_RADIUS*2), pygame.SRCALPHA), 
                                     pygame.Surface((100, 100), pygame.SRCALPHA))
        circle.fill(0), square.fill("white"), circle_o.fill(0)
        pygame.draw.circle(circle, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS)
        pygame.draw.circle(circle_o, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS, OUTLINE_SIZES["t"])

        qcsurf = pygame.Surface((CIRCLE_RADIUS, CIRCLE_RADIUS), pygame.SRCALPHA)
        qcsurf.fill(0)
        pygame.draw.circle(qcsurf, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS, 0, False, True, False, False)
        for rot, name in [(0, "tl"), (270, "tr"), (180, "br"), (90, "bl")]:
            self.ui_atlas.add(pygame.transform.rotate(qcsurf, rot), f"qc_{name}")

        for on, outline in OUTLINE_SIZES.items():
            qcsurf.fill(0)
            pygame.draw.circle(qcsurf, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS, outline, False, True, False, False)
            for rot, name in [(0, "tl"), (270, "tr"), (180, "br"), (90, "bl")]:
                self.ui_atlas.add(pygame.transform.rotate(qcsurf, rot), f"qc_{on}_{name}")
        
        ocsurf = pygame.Surface((CIRCLE_RADIUS*2, CIRCLE_RADIUS*2), pygame.SRCALPHA)
        for on, outline in OUTLINE_SIZES.items():
            ocsurf.fill(0)
            pygame.draw.circle(ocsurf, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS, outline)
            self.ui_atlas.add(ocsurf.copy(), f"co_{on}")
            
        damageoverlay = pygame.transform.scale_by(pygame.image.load(f"assets/images/unlisted/{DAMAGE_OVERLAY}.png").convert_alpha(), 0.4)

        self.ui_atlas.add(damageoverlay, DAMAGE_OVERLAY)
        self.world_atlas.add(circle, "circle"), self.ui_atlas.add(circle, "circle")
        self.world_atlas.add(square, "square"), self.ui_atlas.add(square, "square")
        self.world_atlas.add(circle_o, "circle_o")
        
    def load_folders(self, *names):
        for name in names:
            for file in os.listdir(f"assets/images/{name}"):
                surf = pygame.image.load(f"assets/images/{name}/{file}").convert_alpha()
                self.world_atlas.add(surf, file.split('.')[0])
                
    def load_ui_folders(self, *names):
        for name in names:
            for file in os.listdir(f"assets/images/{name}"):
                surf = pygame.image.load(f"assets/images/{name}/{file}").convert_alpha()
                if name == "icons" and "warning" not in file and "settingsicon" not in file:
                    surf = pygame.transform.scale_by(surf, 0.6)
                self.ui_atlas.add(surf, file.split('.')[0])
        
    def load_named_folders(self, *names):
        for name in names:
            for file in os.listdir(f"assets/images/{name}"):
                surf = pygame.image.load(f"assets/images/{name}/{file}").convert_alpha()
                if name == "stars":
                    surf = pygame.transform.scale_by(surf, 0.3)
                self.world_atlas.add(surf, f"{name}/{file.split('.')[0]}")
        
    def load_player(self):
        player = {}
        adds = ["", "right", "left", "", ""]
        for i, status in enumerate(["idle", "runx", "runx", "runydown", "runyup"]):
            array = TextureArray([], status+adds[i])
            for fn in sorted(os.listdir(f"assets/images/player/{status}"), key=lambda x: (int(x[0]) if x[0].isdecimal() else x)):
                tex = Texture.load(f"assets/images/player/{status}/{fn}", flipx = adds[i]=="left")
                array.add_texture(tex)
            player[status+adds[i]] = array
        return player
    