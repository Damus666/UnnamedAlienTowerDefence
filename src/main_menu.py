from .engine.prelude import *
import random

from .menu_ui import SettingsUI
from . import god
from .consts import *
from .world_props import Tile
from .settings import Tutorial

class MenuEnemy:
    def __init__(self, center, enemy: EnemyData, index):
        self.rect = pygame.FRect((0, 0), MENU_ENEMY_SIZE).move_to(center=center)
        self.hitbox = self.rect.inflate(0.5, 0.5)
        self.pos = pygame.Vector2(center)
        self.index = index
        self.light = Light(center, *enemy.light_data)
        self.light.intensity += 0.5
        god.menu.dynamic_light_batch.add_light(self.light)
        self.light.active = False
        self.rect_obj = RectObj(center, None, MENU_ENEMY_SIZE, None, WORLD_ATLAS, god.assets.get_uvs(enemy.tex_name))
        self.txt_rect_obj = RectObj.null()
        
    def update(self):
        self.pos += pygame.Vector2(1, 0)*MENU_ENEMY_SPEED*camera.dt
        self.rect.center = self.pos
        if self.rect.left > camera.rect.right:
            self.rect.right = camera.rect.left
            self.pos = pygame.Vector2(self.rect.center)
        self.light.rect.center = self.pos
        if god.menu.enemy_index == -1 and self.hitbox.collidepoint(camera.world_mouse):
            self.light.active = True
        else:
            self.light.active = False
        self.hitbox.center = self.rect.center
        self.txt_rect_obj = font.render_single_center(MAIN_FONT, f"{self.index+1}", (self.pos.x, self.rect.bottom+0.5), 2)[0]
        self.rect_obj.update_positions(self.rect.center, None, MENU_ENEMY_SIZE)

class MainMenu(Scene):
    def init(self):
        god.assets.loading_screen()
        god.menu = self
        god.sounds.music_play("menu_music", 0)
        god.settings.tutorial = Tutorial()
        
        self.poral_angle = 0
        self.enemy_index = -1
        self.sel_enemy = None
        self.sel_enemy_rect_obj = RectObj((0, 0), None, MENU_ENEMY_SIZE, None, WORLD_ATLAS)
        self.sel_enemy_light = Light((0, 0), (1, 1, 1), 1, 1)
        self.sel_enemy_light.active = False
        
        self.static_light_batch, self.dynamic_light_batch = LightBatch(), LightBatch(lambda _: True)
        self.static_rects = []
        self.unlit_rects = []
        self.static_top_rects:list[RectObj] = []
        self.static_txt_rects: list[RectObj] = []
        self.settings_static_rects = []
        self.plant_tiles: list[Tile] = []
        self.enemies: list[MenuEnemy] = []

        self.create_bg()
        self.create_title()
        self.add_light_to_plants()
        self.create_enemies()
        self.create_buttons()
        
        self.loading_batch = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        self.unlit_batch = FixedRectsBatch(self.unlit_rects).create_vao(UNLIT_SHADER, *SHADER_UNIFORMS)
        self.settings_batch = FixedRectsBatch(self.settings_static_rects).create_vao(LIT_SHADER, *SHADER_UNIFORMS)
        self.bg_batch = FixedRectsBatch(self.static_rects).create_vao(LIT_SHADER, *SHADER_UNIFORMS)
        self.static_batch = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        self.dynamic_batch = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        
        self.settings = SettingsUI(False)
        self.build()
        
    def create_bg(self):
        for x in range(int(-camera.rect.w/2-1), int(camera.rect.w/2+1)):
            for y in range(int(-camera.rect.h/2-1), int(camera.rect.h/2+1)):
                color = (1, 1, 1, 1)
                if y > camera.rect.bottom-QUIT_SPACE_SIZES[1] and x > camera.rect.right-QUIT_SPACE_SIZES[0]:
                    if random.randint(0, 100) <= LILSTAR_CHANCE*4:
                        self.add_lilstar((x, y))
                    continue
                can_plant = True
                if x > camera.rect.right-QUIT_SPACE_SIZES[0] and y == camera.rect.bottom-QUIT_SPACE_SIZES[1]:
                    color = (0.5, 0.5, 0.5, 1)
                    tile_type = GRASS_TILE
                    can_plant = False
                elif x > camera.rect.right-QUIT_SPACE_SIZES[0] and y == camera.rect.bottom-QUIT_SPACE_SIZES[1]-1:
                    color = (0.5, 0.5, 0.5, 1)
                    tile_type = GRASS_SIDE_TILE
                    can_plant = False
                else:
                    tile_type = GRASS_TILE
                    if y >= -PATH_SIZE//2-PATH_OFFSET and y <= PATH_SIZE//2-PATH_OFFSET:
                        tile_type = ROCK_TILE
                        
                self.static_rects.append(RectObj(None, (x, y), (OBJ_SIZE, OBJ_SIZE), color, WORLD_ATLAS, god.assets.get_uvs(tile_type)))
                
                if y == PATH_SIZE//2+1-PATH_OFFSET:
                    self.static_rects.append(RectObj(None, (x, y), (OBJ_SIZE, OBJ_SIZE), (0.6, 0.6, 0.6, 1), WORLD_ATLAS, god.assets.get_uvs(FLIP_GRASS_TILE)))
                if y == -PATH_SIZE//2-PATH_OFFSET:
                    self.static_rects.append(RectObj(None, (x, y), (OBJ_SIZE, OBJ_SIZE), (0.5, 0.5, 0.5, 1), WORLD_ATLAS, god.assets.get_uvs(HALF_GRASS_TILE)))
                
                if not can_plant:
                    continue
                if tile_type == GRASS_TILE:
                    for noise in [god.settings.cactus_noise, god.settings.spiral_noise, god.settings.grass_plant_noise]:
                        if noise.noise((x, y), 1.5) < noise.activation+0.1:
                            self.add_plant(noise.tile, (x, y))
                            break
                if tile_type == ROCK_TILE:
                    for noise in [god.settings.rove_noise, god.settings.spores_noise]:
                        if noise.noise((x, y), 1.5) < noise.activation+0.1:
                            self.add_plant(noise.tile, (x, y))
                            break
                        
        self.add_dust((random.uniform(camera.rect.right-QUIT_SPACE_SIZES[0]+1, camera.rect.right-1),
                       random.uniform(camera.rect.bottom-QUIT_SPACE_SIZES[1]+1, camera.rect.bottom-1)))
                        
    def add_dust(self, center):
        size = random.uniform(5, 8)
        if random.randint(0, 100) < 50:
            color = DUST1_START.lerp(DUST1_END, random.uniform(0.0, 1.0))
        else:
            color = DUST2_START.lerp(DUST2_END, random.uniform(0.0, 1.0))
        color.a = random.randint(50,100)
        self.unlit_rects.append(RectObj(center, None, (size, size), (color.r/255, color.g/255, color.b/255, color.a/255),
                                            WORLD_ATLAS, god.assets.get_uvs("particle")))
                        
    def add_lilstar(self, topleft):
        pos = (topleft[0]+random.uniform(0.0, OBJ_SIZE-0.3), topleft[1] + random.uniform(0.0, OBJ_SIZE-0.3))
        color = (random.randint(200,255)/255, random.randint(200, 255)/255, random.randint(200, 255)/255, 0.8)
        size = random.uniform(OBJ_SIZE/18, OBJ_SIZE/12)
        self.unlit_rects.append(RectObj(pos, None, (size*3, size*3), color, WORLD_ATLAS, god.assets.get_uvs("particle")))
        self.unlit_rects.append(RectObj(pos, None, (size, size), color, WORLD_ATLAS, god.assets.get_uvs("square")))
                        
    def add_plant(self, plant_tile, topleft):
        topleft = (topleft[0] + random.uniform(-PLANT_OFFSET, PLANT_OFFSET), topleft[1] + random.uniform(-PLANT_OFFSET, PLANT_OFFSET))
        self.plant_tiles.append(Tile(topleft, OBJ_SIZE, plant_tile, False, True))
        self.static_top_rects.append((ro:=RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), (1, 1, 1, 1),
                                            WORLD_ATLAS, god.assets.get_uvs(plant_tile, "plants"))))
        self.settings_static_rects.append(ro)
        
    def add_light_to_plants(self):
        lights_covered = {name: [] for name in CHUNK_LIGHT_DATA.keys()}
        for plant in self.plant_tiles:
            if plant.tile_name not in lights_covered:
                continue
            lights = lights_covered[plant.tile_name]
            is_far = False
            for light_pos in lights:
                if pygame.Vector2(plant.rect.center).distance_to(light_pos) < PLANT_CHUNK_DIST:
                    is_far = True
                    break
            if not is_far:
                self.static_light_batch.add_light(Light(plant.rect.center, *CHUNK_LIGHT_DATA[plant.tile_name]))
                lights_covered[plant.tile_name].append(plant.rect.center)
        
    def create_title(self):
        self.title_center = (0, -camera.rect.h/3.1)
        titlerects = font.render_single_center(MAIN_FONT, TITLE, self.title_center, 10)
        for r in titlerects:
            r._ = True
        self.static_top_rects += titlerects
        self.static_light_batch.add_light(Light(self.title_center, (1, 1, 1), camera.rect.w/2, 0.6))
        charw = font.render_single_width(MAIN_FONT, "J", 10)
        available = [(v-(len(TITLE)-2)//2)*charw for v in list(range(len(TITLE)-2)) if v != len("Evergreen ")-1 and v%2 == 0]
        
        self.static_top_rects += font.render_single(MAIN_FONT, "V 0.2", (camera.rect.left+S, camera.rect.top), 1, "tl", (2, 2, 2, 1))

        for _ in range(6):
            tree = random.choice(TreeData.get_all())
            x = random.choice(available)
            available.remove(x)
            pos = (x, random.choice([self.title_center[1]+1.5, self.title_center[1]-1.5, self.title_center[1]+0.8, self.title_center[1]-0.8]))
            self.static_top_rects.append(ro:=RectObj(None, (pos[0]-tree.size/2, pos[1]-tree.size/2), (tree.size, tree.size), None, WORLD_ATLAS, god.assets.get_uvs(tree.tex_name)))
            self.static_light_batch.add_light(Light(pos, *tree.light_data))
            self.settings_static_rects.append(ro)
        
    def create_enemies(self):
        amount = 8
        enemies = [EnemyData.get(name+"_bot") 
                   for name in ["cian", "pink", "green", "orange", "yellow", 
                                "red", "blue", "purple", "white", "black", "boss"]][:amount]
        space = camera.rect.w/amount+2/amount
        x = -camera.rect.w/2+1
        for i in range(amount):
            enemy = MenuEnemy((x, -PATH_OFFSET), enemies[i], i)
            self.enemies.append(enemy)
            x += space
        self.dynamic_light_batch.add_light(self.sel_enemy_light)
            
        self.portal_rect = pygame.FRect((0, 0), (8, 8)).move_to(center=(0, camera.rect.h/4+1.2-PATH_OFFSET))
        self.portal_obj = RectObj(self.portal_rect.center, None, self.portal_rect.size, None, WORLD_ATLAS, god.assets.get_uvs(EnemyData.get("boss_bot").tex_name))
        self.portal_light = Light(self.portal_rect.center, (1, 0, 0), 10, 1)
        self.dynamic_light_batch.add_light(self.portal_light)
        
        self.static_txt_rects += font.render_single_center(MAIN_FONT, f"{god.lang["main-menu-help"]}", (0, camera.rect.bottom-0.2), 0.8)
    
    def create_buttons(self):
        self.settings_rect = pygame.FRect(0, 0, 5, 5).move_to(center=(-camera.rect.w/4-1.5, camera.rect.h/4+1.2-PATH_OFFSET))
        self.settings_obj = RectObj(self.settings_rect.center, None, self.settings_rect.size, None, UI_ATLAS, god.assets.get_ui_uvs("settingsicon"))
        self.settings_light = Light(self.settings_rect.center, (1, 1, 1), 5, 0.4)
        self.dynamic_light_batch.add_light(self.settings_light)
        self.static_txt_rects += font.render_single_center(MAIN_FONT, f"{god.lang["settings"]}", (self.settings_rect.centerx, self.settings_rect.bottom+0.2), 1.8)
    
        self.quit_rect = pygame.FRect((0, 0), QUIT_SPACE_SIZES).move_to(center=(camera.rect.right-QUIT_SPACE_SIZES[0]/2, camera.rect.bottom-QUIT_SPACE_SIZES[1]/2+0.3))
        self.static_txt_rects += font.render_single_center(MAIN_FONT, f"{god.lang["quit"]}", self.quit_rect.center, 3)
        self.quit_light = Light(self.quit_rect.center, (1, 1, 1), 6, 0.4)
        self.dynamic_light_batch.add_light(self.quit_light)
    
    def build(self):
        self.settings.build()
        self.static_txt_rects = []
        
        self.static_txt_rects += font.render_single_center(MAIN_FONT, f"{god.lang["main-menu-help"]}", (0, camera.rect.bottom-0.2), 0.8)
        self.static_txt_rects += font.render_single_center(MAIN_FONT, f"{god.lang["settings"]}", (self.settings_rect.centerx, self.settings_rect.bottom+0.2), 1.8)
        self.static_txt_rects += font.render_single_center(MAIN_FONT, f"{god.lang["quit"]}", self.quit_rect.center, 3)
        
        self.loading_batch.update_rects(font.render_single_center(MAIN_FONT, f"{god.lang["loading"]}", (0, 0), 8))
        self.static_batch.update_rects(sorted(self.static_top_rects+self.static_txt_rects,
                                                                     key=(lambda r: (r.pos[1]+r.size[1] if not r._ else r.pos[1]+r.size[1]/1.3))))
    
    def loading_screen(self):
        ctx.clear(self.clear_color)
        self.unlit_batch.render()
        self.bg_batch.render()
        self.settings_batch.render()
        self.loading_batch.render()
        camera.tick_window(god.settings.fps)
     
    def start_map(self):
        self.loading_screen()
        
        maps = MapData.get_all()
        index = pygame.math.clamp(self.enemy_index, 0, len(maps)-1)
        god.app.load_scene("World", maps[index])
    
    def event(self, event):
        if event.type == pygame.VIDEORESIZE:
            god.app.screen_buffer.refresh_buffer(event.w, event.h, god.settings.scaled_mul)
            self.build()
        if self.settings.is_open:
            self.settings.event(event)
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            for enemy in self.enemies:
                if enemy.hitbox.collidepoint(camera.world_mouse):
                    self.enemy_index = enemy.index
                    self.sel_enemy = enemy
                    self.sel_enemy_rect_obj.uv = enemy.rect_obj.uv
                    self.sel_enemy_light.active = True
                    self.sel_enemy_light.color = enemy.light.color
                    self.sel_enemy_light.intensity = enemy.light.intensity
                    self.sel_enemy_light.range = enemy.light.range
                    god.sounds.play("click")

            if self.settings_rect.collidepoint(camera.world_mouse):
                self.settings.is_open = True
                self.portal_light.active = False
                self.settings_light.active = False
                god.sounds.play("click")
                
            if self.quit_rect.collidepoint(camera.world_mouse):
                god.app.quit()
                
        if event.type == pygame.MOUSEBUTTONUP:
            if self.enemy_index != -1:
                if self.portal_rect.collidepoint(camera.world_mouse):
                    self.start_map()
            self.enemy_index = -1
            self.sel_enemy = None
            self.sel_enemy_light.active = False
            
    def close_settings(self):
        self.settings.is_open = False
        self.portal_light.active = True
        self.settings_light.active = True
        
    def update(self):
        god.world = None
        
        self.dynamic_light_batch.filter()
        self.dynamic_light_batch.update_buffer()
        if self.settings.is_open:
            self.settings.update()
            return
        
        self.poral_angle += PORTAL_ROT_SPEED*camera.dt*0.5
        self.portal_obj.update_positions(self.portal_rect.center, None, self.portal_rect.size, self.poral_angle)
        self.settings_obj.update_positions(self.settings_rect.center, None, self.settings_rect.size, self.poral_angle)

        if self.enemy_index != -1:
            self.sel_enemy_light.rect.center = camera.world_mouse
            self.sel_enemy_rect_obj.update_positions(camera.world_mouse, None, MENU_ENEMY_SIZE)
            if self.portal_rect.collidepoint(camera.world_mouse):
                self.portal_light.intensity = 1.8
            else:
                self.portal_light.intensity = 1
            self.settings_light.intensity = 0.4
            self.quit_light.intensity = 0.4
        else:
            if self.settings_rect.collidepoint(camera.world_mouse):
                self.settings_light.intensity = 1
            else:
                self.settings_light.intensity = 0.4
            if self.quit_rect.collidepoint(camera.world_mouse):
                self.quit_light.intensity = 0.8
            else:
                self.quit_light.intensity = 0.4
            
            self.portal_light.intensity = 1
            
        for enemy in self.enemies:
            enemy.update()
            
        extra = [self.sel_enemy_rect_obj] if self.enemy_index != -1 else []
        self.dynamic_batch.update_rects([e.rect_obj for e in self.enemies]+[e.txt_rect_obj for e in self.enemies]+[self.portal_obj, self.settings_obj]+extra)
                    
    def render(self):
        LightBatch.upload_uniform(self.static_light_batch, self.dynamic_light_batch, 
                                  LIT_SHADER, god.settings.max_lights)
        
        self.unlit_batch.render()
        self.bg_batch.render()
        if self.settings.is_open:
            self.settings_batch.render()
            self.settings.render()
        else:
            self.static_batch.render()
            self.dynamic_batch.render()

            