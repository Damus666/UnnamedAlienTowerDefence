from .engine.prelude import *
import os

from .consts import *

class Assets:
    def __init__(self):
        self.assets: dict[str, SpriteAtlas|dict[str, TextureArray]] = {}
        
        self.assets["player"] = self.load_player()
        self.assets["world_atlas"] = SpriteAtlas()
        #self.assets["ui_atlas"] = SpriteAtlas()
        
        self.load_folders("tiles", "trees", "buildings", "other", "particles", "enemies")
        self.load_named_folders("plants", "stars")
        self.load_pg()
        
        self.assets["world_atlas"].build("world_atlas")
        #self.assets["ui_atlas"].build("ui_atlas")
        
    def get_uvs(self, name, folder_name=None, flipx=False):
        return self.assets["world_atlas"].get_uvs(name if folder_name is None else f"{folder_name}/{name}", flipx)
        
        
    def get_ui_uvs(self, name, folder_name=None, flipx=False):
        return self.assets["ui_atlas"].get_uvs(name if folder_name is None else f"{folder_name}/{name}", flipx)
        
    def use(self):
        self.assets["world_atlas"].texture.use(WORLD_ATLAS)
        
    def use_ui(self):
        self.assets["ui_atlas"].texture.use(UI_ATLAS)
        
    def load_pg(self):
        circle, circle_o, square = (pygame.Surface((CIRCLE_RADIUS*2, CIRCLE_RADIUS*2), pygame.SRCALPHA), 
                                    pygame.Surface((CIRCLE_RADIUS*2, CIRCLE_RADIUS*2), pygame.SRCALPHA), 
                                     pygame.Surface((10, 10), pygame.SRCALPHA))
        circle.fill(0), square.fill("white"), circle_o.fill(0)
        pygame.draw.circle(circle, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS)
        pygame.draw.circle(circle_o, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS, OUTLINE_W)
        self.assets["world_atlas"].add(circle, "circle")
        self.assets["world_atlas"].add(square, "square")
        self.assets["world_atlas"].add(circle_o, "circle_o")
        
    def load_folders(self, *names):
        for name in names:
            for file in os.listdir(f"assets/images/{name}"):
                surf = pygame.image.load(f"assets/images/{name}/{file}").convert_alpha()
                self.assets["world_atlas"].add(surf, file.split(".")[0])
        
    def load_named_folders(self, *names):
        for name in names:
            for file in os.listdir(f"assets/images/{name}"):
                surf = pygame.image.load(f"assets/images/{name}/{file}").convert_alpha()
                if name == "stars":
                    surf = pygame.transform.scale_by(surf, 0.3)
                self.assets["world_atlas"].add(surf, f"{name}/{file.split(".")[0]}")
        
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
        
    def __getitem__(self, key):
        return self.assets[key]

class OLDAssets:
    def __init__(self):
        self.assets = {}
        
        self.assets["player"] = self.load_player()
        
        for name in ["icons"]:
            self.assets[name] = self.load_folder(name)
            
        for name in ["tiles", "destroy", "tools", "enemies", "stars"]:
            self.assets[name] = self.load_sheet(name)
        
        plants_sheet, trees_sheet = self.load_sheets_size("world", ("plants", 16), ("trees", 32))
        self.assets["plants"] = plants_sheet
        self.assets["trees"] = trees_sheet
        
        items16_sheet, items32_sheet = self.load_sheets_size("items", ("items16", 16), ("items32", 32))
        self.assets["items16"] = items16_sheet
        self.assets["items32"] = items32_sheet
        
        circle_surf = pygame.Surface((CIRCLE_RADIUS*2, CIRCLE_RADIUS*2), pygame.SRCALPHA)
        circle_surf.fill(0)
        pygame.draw.circle(circle_surf, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), CIRCLE_RADIUS)
        square_surf = pygame.Surface((1,1))
        square_surf.fill("white")
        
        quarter_circle_sheet = Spritesheet("quartercircle")
        quarter_circle_surf = pygame.Surface((CIRCLE_RADIUS, CIRCLE_RADIUS), pygame.SRCALPHA)
        quarter_circle_surf.fill(0)
        pygame.draw.circle(quarter_circle_surf, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), (CIRCLE_RADIUS), 0, False, True, False, False)
        for rot, name in [(0, "tl"), (270, "tr"), (180, "br"), (90, "bl")]:
            quarter_circle_sheet.add(pygame.transform.rotate(quarter_circle_surf, rot), name)
        quarter_circle_sheet.build()
        
        outline_circle_sheet = Spritesheet("outlinecircle")
        outline_circle_surf = pygame.Surface((CIRCLE_RADIUS, CIRCLE_RADIUS), pygame.SRCALPHA)
        outline_circle_surf.fill(0)
        self.outline_circle_side_div = CIRCLE_RADIUS/OUTLINE_W
        pygame.draw.circle(outline_circle_surf, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), (CIRCLE_RADIUS), OUTLINE_W, False, True, False, False)
        for rot, name in [(0, "tl"), (270, "tr"), (180, "br"), (90, "bl")]:
            outline_circle_sheet.add(pygame.transform.rotate(outline_circle_surf, rot), name)
        outline_circle_sheet.build()
        
        outline_circle_sheet_b = Spritesheet("outlinecircleb")
        outline_circle_surf_b = pygame.Surface((CIRCLE_RADIUS, CIRCLE_RADIUS), pygame.SRCALPHA)
        outline_circle_surf_b.fill(0)
        self.outline_circle_side_div_b = CIRCLE_RADIUS/OUTLINE_BW
        pygame.draw.circle(outline_circle_surf_b, "white", (CIRCLE_RADIUS, CIRCLE_RADIUS), (CIRCLE_RADIUS), OUTLINE_BW, False, True, False, False)
        for rot, name in [(0, "tl"), (270, "tr"), (180, "br"), (90, "bl")]:
            outline_circle_sheet_b.add(pygame.transform.rotate(outline_circle_surf_b, rot), name)
        outline_circle_sheet_b.build()
        
        self.assets["shapes"] = {
            "circle": Texture.from_surface(circle_surf, "circle"),
            "square": Texture.from_surface(square_surf, "square"),
            "particle": Texture.load("assets/images/other/particle.png"),
            "block": Texture.load("assets/images/other/blockselection.png", "block"),
            "quartercircle": quarter_circle_sheet,
            "outlinecircle": outline_circle_sheet,
            "outlinecircleb": outline_circle_sheet_b
        }
        
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
    
    def load_folder(self, name):
        textures = {}
        for fn in os.listdir(f"assets/images/{name}"):
            tex = Texture.load(f"assets/images/{name}/{fn}")
            textures[tex.name] = tex
        return textures
    
    def load_sheet(self, name):
        sheet = Spritesheet(name)
        for fn in os.listdir(f"assets/images/{name}"):
            sheet.add(pygame.image.load(f"assets/images/{name}/{fn}").convert_alpha(), fn.split(".")[0])
        sheet.build()
        return sheet
    
    def load_sheets_size(self, folder_name, *name_size):
        sheets: dict[int, Spritesheet] = {}
        for name, size in name_size:
            sheets[size] = Spritesheet(name)
        for fn in os.listdir(f"assets/images/{folder_name}"):
            texname = fn.split(".")[0]
            image = pygame.image.load(f"assets/images/{folder_name}/{fn}").convert_alpha()
            size = image.get_width()
            if image.get_height() == size and size in sheets:
                sheets[size].add(image, texname)
        for sheet in sheets.values():
            sheet.build()
        return list(sheets.values())
        
    def __getitem__(self, key):
        return self.assets[key]