import pygame
import sys
import json
import os

SIZES = WIDTH, HEIGHT = 1920, 1080
TITLE = "Evergreen Defense Map Editor"
PANEL_W = WIDTH/5
PANEL_X = WIDTH-PANEL_W
VIEW_W = WIDTH-PANEL_W
VIEW_RECT = pygame.Rect(0, 0, VIEW_W, HEIGHT)

BG_COL = (20, 20, 20)
LBG_COL = (30, 30, 30)
LINE_COL = (60, 60, 60)
WORLD_LINE_COL = (50, 50, 50)
OUTLINE_COL = (100, 100, 100)
BLOCK_UI_SIZE = PANEL_W/5
UI_SIZE_S = PANEL_W/6.5
UNIT_SIZE = 60
UI_ENEMY_SIZE = VIEW_W/30
S = 5
STAGE_LEFT = S+50+50

INCREASE = {
    "wait": 0.5,
    "cooldown": 0.1,
    "xp": 5
}

EXTRA_HEIGHT = 4
OUT_DIR = "assets/maps/"
TOP_BLOCKS = ["spawner", "oxygen", "pos"]
BLOCK_IDS = {
    "rock": 1,
    "grass": 2,
    "iron": 3,
    "copper": 4,
    "titanium": 5,
    "tioplasm": 6
}
REV_BLOCK_IDS = {v:k for k, v in BLOCK_IDS.items()}

def get_image(path):
    img = pygame.transform.scale(pygame.image.load(f"assets/images/{path}.png").convert_alpha(), (32, 32))
    return img

main: "EvergreenDefenseMapEditor" = None

class Stage:
    def __init__(self, name=None, amount=0, xp=0, cooldown=0, wait=0):
        self.name = name
        if name:
            self.name = self.name.replace("_bot", "")
        self.amount = amount
        self.xp = xp
        self.cooldown = cooldown
        self.wait = wait
        
    def draw(self, y, font: pygame.Font, wave:"Wave"):
        wait_surf = font.render(f"Wait: {round(self.wait, 1)}", True, "white")
        wait_rect = wait_surf.get_rect(topleft=(STAGE_LEFT, y))
        main.screen.blit(wait_surf, wait_rect)
        cooldown_surf = font.render(f"Cooldown: {round(self.cooldown, 1)}", True, "white")
        cooldown_rect = cooldown_surf.get_rect(topleft = (STAGE_LEFT+200, y))
        main.screen.blit(cooldown_surf, cooldown_rect)
        xp_surf = font.render(f"XP: {int(self.xp)}", True, "white")
        xp_rect = xp_surf.get_rect(topleft=(STAGE_LEFT+450, y))
        main.screen.blit(xp_surf, xp_rect)
        
        mouse = pygame.mouse.get_pos()
        just_pressed = pygame.key.get_just_pressed()
        
        x = 0
        for i in range(self.amount+1):
            rect = pygame.Rect(STAGE_LEFT+x, y+wait_rect.h+S, UI_SIZE_S, UI_SIZE_S)
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(main.screen, LBG_COL, rect, 0, 5)
            pygame.draw.rect(main.screen, OUTLINE_COL if hover else LINE_COL, rect, 2, 5)
            if i < self.amount:
                main.screen.blit(main.senemy_images[self.name], main.senemy_images[self.name].get_rect(center=rect.center))
                if hover and pygame.mouse.get_pressed()[pygame.BUTTON_MIDDLE-1]:
                    main.change_enemy(self.name)
                if hover and main.clicked:
                    self.amount -= 1
                if hover and pygame.mouse.get_pressed()[pygame.BUTTON_RIGHT-1]:
                    self.name = main.selected_enemy
            else:
                surf = main.font1.render(f"+", True, "white")
                main.screen.blit(surf, surf.get_rect(center=rect.center))
                if main.clicked and hover:
                    if self.name is None:
                        self.name = main.selected_enemy
                    self.amount += 1
                            
            x += UI_SIZE_S+S
            
        txt_surf = main.font1.render(f"{self.amount}", True, "white")
        txt_rect = txt_surf.get_rect(center=(STAGE_LEFT+x+UI_SIZE_S/2, y+wait_rect.h+S+UI_SIZE_S/2))
        main.screen.blit(txt_surf, txt_rect)
        txt_rect = txt_rect.inflate((txt_rect.h+2-txt_rect.w), 2)
        if txt_rect.collidepoint(mouse):
            pygame.draw.rect(main.screen, (80, 80, 80), txt_rect, 1, 7)
            if just_pressed[pygame.K_w] or just_pressed[pygame.K_UP]:
                index = wave.stages.index(self)
                if index > 0:
                    wave.stages.remove(self)
                    wave.stages.insert(index-1, self)
            elif just_pressed[pygame.K_s] or just_pressed[pygame.K_DOWN]:
                index = wave.stages.index(self)
                wave.stages.remove(self)
                wave.stages.insert(index+1, self)
            elif just_pressed[pygame.K_BACKSPACE]:
                wave.stages.remove(self)
                
        
        for name, rect in [("wait", wait_rect), ("cooldown", cooldown_rect), ("xp", xp_rect)]:
            if rect.collidepoint(mouse):
                if just_pressed[pygame.K_a] or just_pressed[pygame.K_LEFT]:
                    setattr(self, name, getattr(self, name)-INCREASE[name])
                elif just_pressed[pygame.K_d] or just_pressed[pygame.K_RIGHT]:
                    setattr(self, name, getattr(self, name)+INCREASE[name])
                if getattr(self, name) < 0:
                    setattr(self, name, 0)
                pygame.draw.rect(main.screen, (80, 80, 80), rect.inflate(6, 3), 1, 7)
        
        y += wait_rect.h+S+S+UI_SIZE_S+S
        return y

class Wave:
    def __init__(self, id, stages=None):
        if stages is None:
            stages = []
        self.stages: list[Stage] = stages
        self.index = id
        self.font = pygame.Font("assets/fonts/alien.ttf", 30)
        self.font2 = pygame.Font("assets/fonts/alien.ttf", 22)
        self.visible = False
        
    def draw(self, y):
        mouse = pygame.mouse.get_pos()
        just_pressed = pygame.key.get_just_pressed()
        extra = f"" if self.visible else f" (hidden)"
        txt_surf = self.font.render(f"Wave {self.index}{extra} ({sum([stage.amount for stage in self.stages])})", True, "white")
        txt_rect = txt_surf.get_rect(topleft = (S+50, y))
        main.screen.blit(txt_surf, txt_rect)
        txt_rect = txt_rect.inflate(6, 0)
        if txt_rect.collidepoint(mouse):
            pygame.draw.rect(main.screen, (80, 80, 80), txt_rect, 1, 7)
            if just_pressed[pygame.K_w] or just_pressed[pygame.K_UP]:
                index = main.waves.index(self)
                if index > 0:
                    main.waves.remove(self)
                    main.waves.insert(index-1, self)
                    main.refresh_waves()
            elif just_pressed[pygame.K_s] or just_pressed[pygame.K_DOWN]:
                index = main.waves.index(self)
                main.waves.remove(self)
                main.waves.insert(index+1, self)
                main.refresh_waves()
            elif just_pressed[pygame.K_BACKSPACE]:
                main.waves.remove(self)
                main.refresh_waves()
            elif main.clicked:
                self.stages.append(Stage("cian", 1, 0, 0.1, 1))
            elif main.clicked_middle:
                self.visible = not self.visible
                
        y += txt_rect.h+S
        if not self.visible:
            return y
        
        for stage in list(self.stages):
            y = stage.draw(y, self.font2, self)
        return y

class EvergreenDefenseMapEditor:
    def __init__(self):
        global main
        main = self
        pygame.init()
        self.screen = pygame.display.set_mode(SIZES)
        self.screen.set_alpha(2)
        self.clock = pygame.Clock()
        
        self.selected_block = "rock"
        self.selected_enemy = "cian"
        self.mode = "map"
        self.pen_size = 1
        self.map_id = 0
        self.zoom = 1
        self.offset = pygame.Vector2()
        self.unit = UNIT_SIZE*self.zoom
        self.drag_start_pos = pygame.Vector2()
        self.drag_start_offset = pygame.Vector2()
        self.block_pos = pygame.Vector2()
        self.view_surf = pygame.Surface((VIEW_W, HEIGHT), pygame.SRCALPHA)
        self.dragging = False
        self.drag_rel = pygame.Vector2()
        self.scroll_offset = 0
        self.waves: list[Wave] = []
        self.clicked = False
        self.clicked_middle = False
        
        self.images = {
            "rock": get_image("tiles/rockblock"),
            "grass": get_image("tiles/grasssideblock"),
            "copper": get_image("tiles/copperoreblock"),
            "iron": get_image("tiles/ironoreblock"),
            "titanium": get_image("tiles/titaniumoreblock"),
            "tioplasm": get_image("tiles/tioplasmoreblock"),
            "spawner": get_image("enemies/boss_bot"),
            "oxygen": get_image("plants/oxygen"),
            "player": get_image("player/idle/idlehigh")
        }
        
        self.enemy_images = {
            name: pygame.transform.scale(pygame.image.load(f"assets/images/enemies/{name}_bot.png").convert_alpha(), (UI_ENEMY_SIZE, UI_ENEMY_SIZE)) 
            for name in ["cian", "pink", "green", "orange", "yellow", "red", "blue", "purple", "white", "black", "boss"]
        }
        
        self.senemy_images = {
            name: pygame.transform.scale(pygame.image.load(f"assets/images/enemies/{name}_bot.png").convert_alpha(), (UI_SIZE_S/1.5, UI_SIZE_S/1.5)) 
            for name in ["cian", "pink", "green", "orange", "yellow", "red", "blue", "purple", "white", "black", "boss"]
        }
        
        circle = pygame.Surface((32, 32), pygame.SRCALPHA)
        circle.fill(0)
        pygame.draw.circle(circle, "blue", (16, 16), 16)
        self.images["pos"] = circle
        self.images["empty"] = pygame.Surface((32, 32))
        self.enemy_images["empty"] = pygame.Surface((32, 32))
        
        self.ui_images = {name:pygame.transform.scale(image, (BLOCK_UI_SIZE/2, BLOCK_UI_SIZE/2)) for name, image in self.images.items()}
        self.unit_images = {name:pygame.transform.scale(image, (self.unit, self.unit)) for name, image in self.images.items()}
        
        self.font1 = pygame.Font("assets/fonts/alien.ttf", 30)
        
        self.button_rects = {
            "load": pygame.Rect(PANEL_X+10, HEIGHT-10-50, (PANEL_W-30)/2, 50),
            "save": pygame.Rect(PANEL_X+20+(PANEL_W-30)/2, HEIGHT-10-50, (PANEL_W-30)/2, 50),
            "x": pygame.Rect(5, 5, 40, 40),
            "map": pygame.Rect(PANEL_X+PANEL_W/2-PANEL_W/4, HEIGHT/2+HEIGHT/6, PANEL_W/2, 50),
            "wave": pygame.Rect(PANEL_X+PANEL_W/2-PANEL_W/4, HEIGHT/2+HEIGHT/6+60, PANEL_W/2, 50),
            "+": pygame.Rect(5, 10+40, 40, 40)
        }
        self.map_id_rects = {}
        w = (PANEL_W-20-5*5)/6
        for i in [0, 1, 2, 3, 4, 5]:
            self.map_id_rects[i] = pygame.Rect(PANEL_X+5+5+5*i+w*i, HEIGHT-20-40-60, w, 40)
            
        self.pen_size_rects = {}
        w = (PANEL_W-20-5*5)/6
        for i, n in enumerate([1, 2, 3, 4, 6, 8, 10, 12, 16, 20, 28, 48]):
            offset = 0
            if i >= 6:
                i -= 6
                offset = 45
            self.pen_size_rects[n] = pygame.Rect(PANEL_X+5+5+5*i+w*i, 40+offset, w, 40)
            
        self.block_rects = {}
        ai = 0
        for image in (self.images.keys()):
            if image not in ["player"]:
                offset = -BLOCK_UI_SIZE/2-5
                i = ai
                if ai >= (len(self.images.keys())-1)/2:
                    i -= (len(self.images.keys())-1)//2
                    offset = BLOCK_UI_SIZE/2+5
                self.block_rects[image] = pygame.Rect(PANEL_X+PANEL_W/2-BLOCK_UI_SIZE/2+offset, 
                                        20+40+40+40+60+BLOCK_UI_SIZE*i+5*i, BLOCK_UI_SIZE, BLOCK_UI_SIZE)
                ai += 1
                
        self.enemy_rects = {}
        ai = 0
        for image in self.enemy_images.keys():
            offset = -BLOCK_UI_SIZE/2-5
            i = ai
            if ai >= len(self.enemy_images.keys())/2:
                i -= (len(self.enemy_images.keys()))//2
                offset = BLOCK_UI_SIZE/2 +5
                
            self.enemy_rects[image] = pygame.Rect(PANEL_X+PANEL_W/2-BLOCK_UI_SIZE/2+offset,
                                                  40+60+BLOCK_UI_SIZE*i+5*i, BLOCK_UI_SIZE, BLOCK_UI_SIZE)
            ai += 1
        
        self.blocks = {}
        self.top_blocks = {}
        self.load()
        
    def refresh_waves(self):
        for i, wave in enumerate(self.waves):
            wave.index = i
        
    def update_map(self):
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        
        unit = self.zoom*UNIT_SIZE
        if unit != self.unit:
            self.unit = unit
            self.unit_images = {name:pygame.transform.scale(image, (unit+1, unit+1)) for name, image in self.images.items()}
            self.update_draw()
        
        if pygame.mouse.get_pressed()[pygame.BUTTON_MIDDLE-1] and mouse.x < VIEW_W:
            self.dragging = True
            rel = -self.drag_start_pos+mouse
            self.drag_rel = rel
            self.offset = self.drag_start_offset+rel
        else:
            if self.dragging:
                self.update_draw()
            self.dragging = False
            self.drag_rel = pygame.Vector2()
            
        fx = (pygame.math.clamp(mouse.x, 0, VIEW_W)-(self.offset.x+VIEW_W/2))/self.unit
        bx = int(fx) if fx > 0 else int(fx)-1
        fy = (mouse.y-(self.offset.y+HEIGHT/2))/self.unit
        by = int(fy) if fy > 0 else int(fy)-1
        self.block_pos = pygame.Vector2(bx, by)
        
        left, right = pygame.mouse.get_pressed()[pygame.BUTTON_LEFT-1], pygame.mouse.get_pressed()[pygame.BUTTON_RIGHT-1]
        if (left or right) and mouse.x < VIEW_W:
            positions = []
            if self.selected_block not in TOP_BLOCKS:
                for i in range(-self.pen_size//2, self.pen_size//2):
                    for j in range(-self.pen_size//2, self.pen_size//2):
                        positions.append((int(self.block_pos.x+i), int(self.block_pos.y+j)))
            else:
                positions = [(int(self.block_pos.x), int(self.block_pos.y))]
            for pos in positions:
                if self.selected_block in TOP_BLOCKS:
                    if not right:
                        self.top_blocks[pos] = self.selected_block
                    else:
                        if pos in self.top_blocks:
                            del self.top_blocks[pos]
                else:
                    if not right:
                        self.blocks[pos] = self.selected_block
                    else:
                        if pos in self.blocks:
                            del self.blocks[pos]
            if right:
                positions = []
            self.update_draw(positions)
                            
        pygame.display.set_caption(f"{TITLE} - {int(self.clock.get_fps())} FPS")
        
    def draw_map(self):
        if self.zoom > 0.2:
            line_amountx = VIEW_W/self.unit + 1
            startx = (self.offset.x+VIEW_W/2)%self.unit
            for i in range(int(line_amountx)):
                pygame.draw.line(self.screen, WORLD_LINE_COL, (startx+self.unit*i, 0), (startx+self.unit*i, HEIGHT), 1)
                
            line_amounty = HEIGHT/self.unit + 1
            starty = (self.offset.y+HEIGHT/2)%self.unit
            for i in range(int(line_amounty)):
                pygame.draw.line(self.screen, WORLD_LINE_COL, (0, starty+self.unit*i), (VIEW_W, starty+self.unit*i), 1)
                
            pygame.draw.circle(self.screen, "white", (self.offset.x+VIEW_W/2, self.offset.y+HEIGHT/2), 2)
                    
        self.screen.blit(self.view_surf, self.drag_rel)
        
    def update_draw(self, positions=None):
        if positions is None:
            positions = []
        if len(positions) <= 0:
            self.view_surf.fill(0)
            
        vec1 = pygame.Vector2(1, 1)
        offsetvec = pygame.Vector2(VIEW_W/2+self.offset.x, HEIGHT/2+self.offset.y)
        
        for pos, name in self.blocks.items():
            if len(positions) > 0 and pos not in positions:
                continue
            topleft = ((pos[0]+1)*self.unit, (pos[1]+1)*self.unit)+offsetvec
            if (VIEW_RECT.collidepoint(topleft) or VIEW_RECT.collidepoint((topleft.x+self.unit, topleft.y+self.unit)) or
                VIEW_RECT.collidepoint((topleft.x, topleft.y+self.unit)) or VIEW_RECT.collidepoint((topleft.x+self.unit, topleft.y))):
                self.view_surf.blit(self.unit_images[name], topleft)
            
        for pos, name in self.top_blocks.items():
            topleft = (pygame.Vector2(pos))*self.unit+offsetvec
            if (VIEW_RECT.collidepoint(topleft) or VIEW_RECT.collidepoint((topleft.x+self.unit, topleft.y+self.unit)) or
                VIEW_RECT.collidepoint((topleft.x, topleft.y+self.unit)) or VIEW_RECT.collidepoint((topleft.x+self.unit, topleft.y))):
                self.view_surf.blit(self.unit_images[name], topleft)
        
        self.view_surf.blit(self.unit_images["player"], (self.offset.x+VIEW_W/2-self.unit/2, self.offset.y+HEIGHT/2-self.unit/2))
    
    def draw_wave(self):
        y = self.scroll_offset+S
        for wave in list(self.waves):
            y = wave.draw(y)
            
        max_time = round(sum([sum([stage.wait+stage.cooldown*stage.amount for stage in wave.stages])+45 for wave in self.waves])/60)
        min_time = round(sum([sum([stage.wait+stage.cooldown*stage.amount for stage in wave.stages]) for wave in self.waves])/60)
        surf = self.font1.render(f"Map could last from ~{min_time} minutes to ~{max_time} minutes", True, "white")
        rect = surf.get_rect(topleft=(S+50, y))
        self.screen.blit(surf, rect)
            
        if self.clicked:
            self.clicked = False
        if self.clicked_middle:
            self.clicked_middle = False
    
    def draw_ui(self):
        mouse = pygame.mouse.get_pos()
        pygame.draw.rect(self.screen, BG_COL, (PANEL_X, 0, PANEL_W, HEIGHT))
        pygame.draw.line(self.screen, LINE_COL, (PANEL_X-2, 0), (PANEL_X-2, HEIGHT), 3)
        
        for txt, rect in self.button_rects.items():
            extra_hover = False
            if txt == "+" and self.mode == "map":
                continue
            if txt in ["map", "wave"]:
                if self.mode == txt:
                    extra_hover = True
                txt += " mode"

            pygame.draw.rect(self.screen, LBG_COL, rect, 0, 5)
            pygame.draw.rect(self.screen, OUTLINE_COL if rect.collidepoint(mouse) or extra_hover else LINE_COL, rect, 2, 5)
            txt_surf = self.font1.render(txt.title(), True, "white")
            self.screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
            
        txt_surf = self.font1.render("map id".title(), True, "white")
        self.screen.blit(txt_surf, txt_surf.get_rect(center=(PANEL_X+PANEL_W/2, self.map_id_rects[0].top-20)))
            
        for i, rect in self.map_id_rects.items():
            pygame.draw.rect(self.screen, LBG_COL, rect, 0, 5)
            pygame.draw.rect(self.screen, OUTLINE_COL if rect.collidepoint(mouse) or self.map_id==i else LINE_COL, rect, 2, 5)
            txt_surf = self.font1.render(str(i), True, "white")
            self.screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
        
        if self.mode == "map":
            txt_surf = self.font1.render("pen size".title(), True, "white")
            self.screen.blit(txt_surf, txt_surf.get_rect(center=(PANEL_X+PANEL_W/2, self.pen_size_rects[1].top-20)))
                
            for i, rect in self.pen_size_rects.items():
                pygame.draw.rect(self.screen, LBG_COL, rect, 0, 5)
                pygame.draw.rect(self.screen, OUTLINE_COL if rect.collidepoint(mouse) or self.pen_size==i else LINE_COL, rect, 2, 5)
                txt_surf = self.font1.render(str(i), True, "white")
                self.screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
            
            txt_surf = self.font1.render("selected".title(), True, "white")
            self.screen.blit(txt_surf, txt_surf.get_rect(center=(PANEL_X+PANEL_W/2, self.block_rects["rock"].top-30)))
            
            for name, rect in self.block_rects.items():
                pygame.draw.rect(self.screen, LBG_COL, rect, 0, 5)
                pygame.draw.rect(self.screen, OUTLINE_COL if (rect.collidepoint(mouse) or self.selected_block==name) and name != "empty" else LINE_COL, rect, 2, 5)
                if name != "empty":
                    self.screen.blit(self.ui_images[name], self.ui_images[name].get_rect(center=rect.center))
                
            txt_surf = self.font1.render(f"Block Pos: {int(self.block_pos.x)}x, {int(self.block_pos.y)}y", True, "white")
            self.screen.blit(txt_surf, txt_surf.get_rect(center=(PANEL_X+PANEL_W/2, self.block_rects["empty"].bottom+40)))
        elif self.mode == "wave":
            txt_surf = self.font1.render("selected".title(), True, "white")
            self.screen.blit(txt_surf, txt_surf.get_rect(center=(PANEL_X+PANEL_W/2, list(self.enemy_rects.values())[0].top-30)))
            
            for name, rect in self.enemy_rects.items():
                pygame.draw.rect(self.screen, LBG_COL, rect, 0, 5)
                pygame.draw.rect(self.screen, OUTLINE_COL if (rect.collidepoint(mouse) or self.selected_enemy==name) and name != "empty" else LINE_COL, rect, 2, 5)
                if name != "empty":
                    self.screen.blit(self.enemy_images[name], self.enemy_images[name].get_rect(center=rect.center))

    def change_map_id(self, id):
        self.map_id = id
        
    def change_pen_size(self, size):
        self.pen_size = size
        
    def change_selected(self, name):
        if name == "empty":
            return
        self.selected_block = name
        
    def change_enemy(self, name):
        if name == "empty":
            return
        self.selected_enemy = name
        
    def x(self):
        pygame.quit()
        sys.exit()
    
    def load(self):
        self.blocks = {}
        self.top_blocks = {}
        self.waves = []
        
        try:
            with open(f"{OUT_DIR}{self.map_id}.json", "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"Map {self.map_id} does not exist yet")
            
        for pos, id in data["floor"].items():
            x, y = pos.split(";")
            x, y = int(x), int(y)
            self.blocks[(x, y)] = REV_BLOCK_IDS[id]
            
        for pos in data["oxygen"]:
            self.top_blocks[tuple(pos)] = "oxygen"
        for pos in data["pos"]:
            self.top_blocks[tuple(pos)] = "pos"
        if data["spawn"] is not None:
            self.top_blocks[tuple(data["spawn"])] = "spawner" 
            
        try:
            with open(f"assets/scriptables/maps/map{self.map_id}.json", "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"Map {self.map_id} does not have a scriptable object associated with it yet")
            
        for i, wave in enumerate(data["waves"]):
            stages = []
            for stage in wave:
                stages.append(Stage(stage["enemy"], stage["amount"], stage["xp"], stage["cooldown"], stage["wait"]))
            self.waves.append(Wave(i, stages))
        
        self.update_draw()
        
    def save(self):
        data = {
            "floor": {},
            "height": {},
            "spawn": None,
            "pos": [],
            "collision": [],
            "oxygen": []
        }
        for (x, y), name in self.blocks.items():
            data["floor"][f"{x};{y}"] = BLOCK_IDS[name]
            up = (x, y-1)
            left = (x-1, y)
            right = (x+1, y)
            bottom = (x, y+1)
            for dir in [up, left, right]:
                if dir not in self.blocks:
                    data["collision"].append(dir)
            if bottom not in self.blocks:
                for i in range(1, EXTRA_HEIGHT+1):
                    data["height"][f"{x};{y+i}"] = BLOCK_IDS[name]
                    data["collision"].append(bottom)
                    
        for (x, y), name in self.top_blocks.items():
            if name == "pos":
                data["pos"].append((x, y))
            elif name == "spawner":
                data["spawn"] = (x, y)
            elif name == "oxygen":
                data["oxygen"].append((x, y))
        
        if os.path.exists(f"{OUT_DIR}{self.map_id}.json"):
            with open(f"{OUT_DIR}{self.map_id}.json", "r") as old_file:
                old_data = old_file.read()
            with open(f"{OUT_DIR}backup/{self.map_id}.json", "w") as backup_file:
                backup_file.write(old_data)
                print(f"Saved backup for map {self.map_id} in maps/backup/{self.map_id}.json")
                
        with open(f"{OUT_DIR}{self.map_id}.json", "w") as file:
            json.dump(data, file)
            
        if not os.path.exists(f"assets/scriptables/maps/map{self.map_id}.json"):
            print(f"Fatal Warning: Cannot save wave data for map {self.map_id} if the scriptable object file is missing")
            return
        
        with open(f"assets/scriptables/maps/map{self.map_id}.json", "r") as old_waved_file:
            old_waved = old_waved_file.read()
            
        with open(f"{OUT_DIR}backup/scriptable{self.map_id}.json", "w") as backup_waved_file:
            backup_waved_file.write(old_waved)
            print(f"Saved scriptable backup for map {self.map_id} in maps/backup/scriptable{self.map_id}.json")
            
        waved = json.loads(old_waved)
        waves = [[{"wait": stage.wait, "cooldown": stage.cooldown, "xp": stage.xp, "amount": stage.amount, "enemy": stage.name+"_bot"} 
                  for stage in wave.stages if stage.name is not None] for wave in self.waves]
        waved["waves"] = waves
        
        with open(f"assets/scriptables/maps/map{self.map_id}.json", "w") as waved_file:
            json.dump(waved, waved_file)
            
    def map(self):
        self.mode = "map"
        
    def wave(self):
        self.mode = "wave"
            
    def event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_MIDDLE:
                self.drag_start_pos = pygame.Vector2(event.pos)
                self.drag_start_offset = self.offset.copy()
            
            if event.button == pygame.BUTTON_LEFT:
                self.clicked = True
                for name, rect in self.button_rects.items():
                    if rect.collidepoint(event.pos):
                        if name == "+":
                            if self.mode == "wave":
                                wave = Wave(len(self.waves))
                                wave.visible = True
                                self.waves.append(wave)
                        else:
                            getattr(self, name)()
                for id, rect in self.map_id_rects.items():
                    if rect.collidepoint(event.pos):
                        self.change_map_id(id)
                if self.mode == "map":
                    for size, rect in self.pen_size_rects.items():
                        if rect.collidepoint(event.pos):
                            self.change_pen_size(size)
                    for name, rect in self.block_rects.items():
                        if rect.collidepoint(event.pos):
                            self.change_selected(name)
                elif self.mode == "wave":
                    for name, rect in self.enemy_rects.items():
                        if rect.collidepoint(event.pos):
                            self.change_enemy(name)
            elif event.button == pygame.BUTTON_MIDDLE:
                self.clicked_middle = True
            
        elif event.type == pygame.MOUSEWHEEL:
            if pygame.mouse.get_pos()[0] < VIEW_W:
                if self.mode == "map":
                    self.zoom += (event.y*0.1)*self.zoom
                    self.zoom = pygame.math.clamp(self.zoom, 0.09, 5)
                else:
                    self.scroll_offset += (event.y*15)
                    if self.scroll_offset > 0:
                        self.scroll_offset = 0             
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.event(event)
            
            if self.mode == "map":
                self.screen.fill(0)
            else:
                self.screen.fill((10, 10, 10))
            
            if self.mode == "map":
                self.update_map()
                self.draw_map()
            elif self.mode == "wave":
                self.draw_wave()
            self.draw_ui()
            
            self.clock.tick(120)
            pygame.display.flip()

if __name__ == "__main__":
    EvergreenDefenseMapEditor().run()
