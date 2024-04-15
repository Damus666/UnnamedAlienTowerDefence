from .engine.prelude import *
import random
import noise
import json
import typing

from .consts import *
from .enemy import Enemy
from .particle import MovingParticle
from . import god

class NoiseSettings:
    def __init__(self, octaves, scale, activation, tile, seed=None):
        self.seed = random.randint(0, 9999)
        self.octaves = octaves
        self.scale = scale
        self.activation = activation
        self.tile = tile
        
    def noise(self, xy):
        return noise.snoise2(xy[0]*self.scale+self.seed, xy[1]*self.scale+self.seed, self.octaves)
        
class PlantNoiseSettings(NoiseSettings):
    def __init__(self, activation, tile, seed=None):
        super().__init__(PLANT_OCTAVES, PLANT_SCALE, activation, tile, seed)
        
class Tile:
    def __init__(self, topleft, size, tile_name, is_floor=False, is_plant=False, is_ore=False, rect_obj=None):
        self.tile_name, self.is_floor, self.is_plant, self.is_height, self.is_ore = tile_name, is_floor, is_plant, not is_floor, is_ore
        self.topleft = pygame.Vector2(topleft)
        self.rect = pygame.FRect(self.topleft, (size, size))
        self.rect_obj = rect_obj
        
class BubbleSpawner:
    def __init__(self, pos):
        self.pos = (pos[0], pos[1]-0.11)
        self.last_bubble = camera.get_ticks()
        
    def update(self):
        if camera.get_ticks()-self.last_bubble > 0.15*1000:
            self.last_bubble = camera.get_ticks()
            dir = (random.uniform(-0.19, 0.19), -1)
            size = (random.uniform(0.11, 0.31))
            god.world.add_uparticle(MovingParticle(self.pos, (size, size), dir, 3.5, random.uniform(0.8, 1.2), "bubble"))
        
class EnemyWaveSpawner:
    def __init__(self):
        self.map = god.world.map
        self.waves_amount = len(god.world.map.waves)
        self.wave_stages = god.world.map.waves[0]
        self.current_stage = self.wave_stages[0]
        self.stage_idx = 0
        self.stages_amount = len(self.wave_stages)
        self.wave_idx = 0
        self.wave_active = False
        self.wave_end_time = camera.get_ticks()
        self.map_complete = False
        self.spawned_emenies = 0
        self.killed_enemies = 0
        self.stage_active = True
        self.stage_end_time = camera.get_ticks()
        self.stages_completed = False
        self.stage_spanwed_enemies = 0
        self.last_enemy = 0
        self.wave_enemies_amount = 1
        self.wave_complete_time = -9999
        
    def update(self):
        if self.map_complete:
            return
        if not self.wave_active:
            if camera.get_ticks() - self.wave_end_time > WAVE_COOLDOWN*1000:
                self.start_wave()
        else:
            if not self.stages_completed:
                if self.stage_active:
                    if self.stage_spanwed_enemies < self.current_stage["enemy_amount"]:
                        if camera.get_ticks() - self.last_enemy > self.current_stage["spawn_cooldown"]*1000:
                            self.spawn_enemy()
                    else:
                        self.end_stage()
                else:
                    if camera.get_ticks() - self.stage_end_time > self.current_stage["wait_time"]*1000:
                        self.start_stage()
            if self.spawned_emenies > 0 and self.killed_enemies == self.spawned_emenies:
                self.end_wave()
                
    def spawn_enemy(self):
        self.last_enemy = camera.get_ticks()
        enemy = Enemy(EnemyData.get(self.current_stage["enemy_name"]), god.world.builder.portal_tile.rect.center)
        god.world.add_enemy(enemy)
        self.spawned_emenies += 1
        self.stage_spanwed_enemies += 1
        
    def enemy_destroyed(self):
        self.killed_enemies += 1
        god.world.ui.update_static()
                
    def end_stage(self):
        self.stage_idx += 1
        if self.stage_idx >= self.stages_amount:
            self.stages_completed = True
            return
        god.player.add_xp(self.current_stage["xp"])
        self.current_stage = self.wave_stages[self.stage_idx]
        self.stage_active = False
        self.stage_end_time = camera.get_ticks()
        
    def start_stage(self):
        self.stage_active = True
        self.stage_spanwed_enemies = 0
        self.last_enemy = camera.get_ticks()
                
    def start_wave(self):
        self.wave_active = True
        self.stage_active = True
        self.wave_enemies_amount = sum([stage["enemy_amount"] for stage in god.world.map.waves[self.wave_idx]])
        god.world.ui.update_static()
        
    def end_wave(self):
        self.wave_idx += 1
        if self.wave_idx >= self.waves_amount:
            self.map_complete = True
            self.wave_idx -= 1
            god.player.celebrate()
            self.wave_complete_time = camera.get_ticks()
            return
        god.player.add_xp(WAVE_XP*god.player.level)
        self.wave_stages = god.world.map.waves[self.wave_idx]
        self.wave_active = False
        self.wave_end_time = camera.get_ticks()
        self.current_stage = self.wave_stages[0]
        self.stage_idx = 0
        self.stages_amount = len(self.wave_stages)
        self.stages_completed = False
        self.spawned_emenies = 0
        self.killed_enemies = 0
        god.world.ui.update_static()
        
class WorldBuilder:
    def __init__(self):
        self.dust_rect_objs, self.tile_rect_objs, self.plant_rect_objs = [], [], []
        
        self.grass_plant_noise = PlantNoiseSettings(-0.5, GRASS_PLANT_TILE)
        self.spiral_noise = PlantNoiseSettings(-0.6, SPIRAL_TILE)
        self.cactus_noise = PlantNoiseSettings(-0.67, CACTUS_TILE)
        self.flowers_noise = PlantNoiseSettings(-0.67, FLOWERS_TILE)
        self.spores_noise = PlantNoiseSettings(-0.65, SPORES_TILE)
        self.rove_noise = NoiseSettings(ROVE_OCTAVES, ROVE_SCALE, -0.62, ROVE_TILE)
        
    def build(self):
        self.build_asteroid()
        self.add_spawner()
        self.add_base()
        self.add_oxygens()
        self.add_light_to_plants()
        
        self.dust_rects_batch = FixedRectsBatch(self.dust_rect_objs, False).create_vao(UNLIT_SHADER, *SHADER_UNIFORMS)
        self.tile_rects_batch = FixedRectsBatch(self.tile_rect_objs+self.plant_rect_objs, False).create_vao(LIT_SHADER, *SHADER_UNIFORMS)
                
    def render(self):
        self.dust_rects_batch.render()
        self.tile_rects_batch.render()
                
    def add_spawner(self):
        self.portal_tile = Tile((god.world.map_loader.spawn[0]-SPAWNER_SIZE/4, god.world.map_loader.spawn[1]-SPAWNER_SIZE/4), SPAWNER_SIZE, SPAWNER_TILE, is_plant=True)
        rect_obj=RectObj(self.portal_tile.rect.center, None, self.portal_tile.rect.size, PORTAL_COL, 
                                            WORLD_ATLAS, god.assets.get_uvs(SPAWNER_TILE))
        self.portal_tile.rect_obj = rect_obj
        god.world.can_be_above_unlit.append(self.portal_tile)
        self.spawner_light = Light(self.portal_tile.rect.center, *SPAWNER_LIGHT_DATA)
        god.world.add_static_light(self.spawner_light)
        
        self.portalframe_tile = Tile((0, 0), SPAWNER_SIZE*1.1, PORTALFRAME_TILE)
        self.portalframe_tile.rect.center = (self.portal_tile.rect.centerx, self.portal_tile.rect.centery+0.17)
        self.plant_rect_objs.append(ro:=RectObj(self.portalframe_tile.rect.center, None, self.portalframe_tile.rect.size, None, WORLD_ATLAS, god.assets.get_uvs(PORTALFRAME_TILE)))
        god.world.can_be_above.append(self.portalframe_tile)
        self.portalframe_tile.rect_obj = ro
        
        hitbox = pygame.FRect(0, 0, self.portal_tile.rect.w/1.4, OBJ_SIZE/2)
        hitbox.midbottom = self.portalframe_tile.rect.midbottom
        god.world.collision_rects.append(hitbox)
        self.portal_hitbox = hitbox
        
    def add_base(self):
        self.base_tile = Tile((god.world.follow_pos[-1][0]-BASE_SIZE/2, god.world.follow_pos[-1][1]-BASE_SIZE), BASE_SIZE, BASE_TILE)
        god.world.can_be_above.append(self.base_tile)
        self.plant_rect_objs.append(ro:=RectObj(self.base_tile.rect.center, None, self.base_tile.rect.size, None, WORLD_ATLAS, god.assets.get_uvs(BASE_TILE)))
        god.world.add_static_light(Light(self.base_tile.rect.center, *BASE_LIGHT_DATA))
        self.base_tile.rect_obj = ro
        
        hitbox = pygame.FRect(0, 0, self.base_tile.rect.w, 2)
        hitbox.midbottom = self.base_tile.rect.midbottom
        god.world.collision_rects.append(hitbox)
        
    def add_oxygens(self):
        for topleft in god.world.map_loader.oxygen_positions:
            tile = Tile((topleft[0]-OXYGEN_SIZE/4, topleft[1]-OXYGEN_SIZE/4), OXYGEN_SIZE, OXYGEN_TILE, is_plant=True)
            god.world.oxygen_tiles.append(tile), god.world.plant_tiles.append(tile), god.world.can_be_above.append(tile)
            self.plant_rect_objs.append(rectobj:=RectObj(tile.rect.center, None, tile.rect.size, None,
                                                         WORLD_ATLAS, god.assets.get_uvs(OXYGEN_TILE, "plants")))
            tile.rect_obj = rectobj
            god.world.bubble_spawners.append(BubbleSpawner(tile.rect.center))
        self.plant_rect_objs.sort(key=lambda x: x.pos[1])
        
    def build_asteroid(self):
        for tx in range(god.world.map_loader.min_x-MAP_PADDING, god.world.map_loader.max_x+MAP_PADDING):
            for ty in range(god.world.map_loader.min_y-MAP_PADDING, god.world.map_loader.max_y+MAP_PADDING):
                topleft = (tx, ty)
                if not god.world.map_loader.has_tile(topleft):
                    if random.randint(0, 100) <= LILSTAR_CHANCE:
                        self.add_lilstar(topleft)
                    elif random.randint(0, DUST_CHANCE_RANGE) <= 1:
                        self.add_dust(topleft)
                    elif random.randint(0, STAR_CHANCE_RANGE) <= 1:
                        self.add_star(topleft)
                else:
                    tex_name, is_height, block_id = god.world.map_loader.tile_data(topleft)
                    self.add_floor(topleft, tex_name) if not is_height else self.add_height(topleft, tex_name)
                    self.add_depth(topleft, tex_name)
                            
                    if block_id == LOAD_GRASS and not is_height:
                        for noise in [self.cactus_noise, self.flowers_noise, self.spiral_noise, self.grass_plant_noise]:
                            if noise.noise(topleft) < noise.activation:
                                self.add_plant(noise.tile, topleft)
                                break
                    if block_id == LOAD_ROCK and topleft[1] > god.world.map_loader.min_y+10:
                        for noise in [self.rove_noise, self.spores_noise]:
                            if noise.noise(topleft) < noise.activation:
                                self.add_plant(noise.tile, topleft)
                                break
                            
    def add_depth(self, topleft, tex_name):
        up = (topleft[0], topleft[1]-1)
        if tex_name in ROCKY_TILES:
            if god.world.map_loader.has_tile(up) and god.world.map_loader.tile_data(up)[-1] not in LOAD_ROCKY:
                self.add_height(topleft, HALF_GRASS_TILE, False)
                god.world.jump_down_rects.append(pygame.FRect(topleft, (OBJ_SIZE, HALF_COLLIDER_H)))
        if tex_name == GRASS_TILE:
            if not god.world.map_loader.has_tile(up) or god.world.map_loader.tile_data(up)[-1] != LOAD_GRASS:
                self.add_colored(topleft, FLIP_GRASS_TILE, (0.6, 0.6, 0.6, 1))
                god.world.jump_up_rects.append(pygame.FRect(topleft, (OBJ_SIZE, HALF_COLLIDER_H)))
        
    def add_light_to_plants(self):
        lights_covered = {name: [] for name in CHUNK_LIGHT_DATA.keys()}
        for plant in god.world.plant_tiles:
            if plant.tile_name not in lights_covered:
                continue
            lights = lights_covered[plant.tile_name]
            is_far = False
            for light_pos in lights:
                if pygame.Vector2(plant.rect.center).distance_to(light_pos) < PLANT_CHUNK_DIST:
                    is_far = True
                    break
            if not is_far:
                god.world.add_static_light(Light(plant.rect.center, *CHUNK_LIGHT_DATA[plant.tile_name]))
                lights_covered[plant.tile_name].append(plant.rect.center)
                
    
        
    def add_dust(self, topleft):
        size = random.uniform(16/0.8, 16/0.3)
        if random.randint(0, 100) < 50:
            color = DUST1_START.lerp(DUST1_END, random.uniform(0.0, 1.0))
        else:
            color = DUST2_START.lerp(DUST2_END, random.uniform(0.0, 1.0))
        color.a = random.randint(50,100)
        self.dust_rect_objs.append(RectObj(topleft, None, (size, size), (color.r/255, color.g/255, color.b/255, color.a/255),
                                            WORLD_ATLAS, god.assets.get_uvs("particle")))
        
    def add_star(self, topleft):
        size = random.uniform(3.1, 6.1)
        name = random.choice(list(STAR_COLORS.keys()))
        self.dust_rect_objs.append(RectObj(topleft, None, (size*2.2, size*2.2), STAR_COLORS[name], WORLD_ATLAS, god.assets.get_uvs("particle")))
        self.dust_rect_objs.append(RectObj(topleft, None, (size, size), None, WORLD_ATLAS, god.assets.get_uvs(name, "stars")))
        
    def add_lilstar(self, topleft):
        pos = (topleft[0]+random.uniform(0.0, OBJ_SIZE-0.3), topleft[1] + random.uniform(0.0, OBJ_SIZE-0.3))
        color = (random.randint(200,255)/255, random.randint(200, 255)/255, random.randint(200, 255)/255, 0.8)
        size = random.uniform(OBJ_SIZE/18, OBJ_SIZE/12)
        self.dust_rect_objs.append(RectObj(pos, None, (size*3, size*3), color, WORLD_ATLAS, god.assets.get_uvs("particle")))
        self.dust_rect_objs.append(RectObj(pos, None, (size, size), color, WORLD_ATLAS, god.assets.get_uvs("square")))
        
    def add_floor(self, topleft, tex_name):
        self.tile_rect_objs.append(RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), (1, 1, 1, 1), 
                            WORLD_ATLAS, god.assets.get_uvs(tex_name)))
        god.world.floor_tiles[f"{int(topleft[0])};{int(topleft[1])}"] = (Tile(topleft, OBJ_SIZE, tex_name, True, False, False,))
        
    def add_colored(self, topleft, tex_name, color):
        self.tile_rect_objs.append(RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), color, 
                            WORLD_ATLAS, god.assets.get_uvs(tex_name)))
        
    def add_height(self, topleft, tex_name, add_tile = True):
        self.tile_rect_objs.append(RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), (0.5, 0.5, 0.5, 1), 
                            WORLD_ATLAS, god.assets.get_uvs(tex_name)))
        if add_tile:
            god.world.height_tiles[f"{int(topleft[0])};{int(topleft[1])}"] = Tile(topleft, OBJ_SIZE, tex_name, False, False, False)
    
    def add_plant(self, plant_tile, topleft):
        topleft = (topleft[0] + random.uniform(-PLANT_OFFSET, PLANT_OFFSET), topleft[1] + random.uniform(-PLANT_OFFSET, PLANT_OFFSET))
        self.plant_rect_objs.append((rect_obj:=RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), (1, 1, 1, 1),
                                            WORLD_ATLAS, god.assets.get_uvs(plant_tile, "plants"))))
        god.world.plant_tiles.append(tile:=Tile(topleft, OBJ_SIZE, plant_tile, is_plant=True, rect_obj=rect_obj))
        if plant_tile not in [ROVE_TILE, SPORES_TILE]:
            god.world.can_be_above.append(tile)
            
    def free_buffers(self):
        self.dust_rects_batch.free_rect_objs()
        self.dust_rect_objs = []
        self.tile_rect_objs = []
        self.plant_rect_objs = []
        
class MapLoader:
    def __init__(self, map: MapData):
        with open(map.data_path, "r") as file:
            data = json.load(file)
            
        self.collisions = [pygame.FRect(pos, (OBJ_SIZE, OBJ_SIZE)) for pos in data["collision"]]
        self.spawn = data["spawn"]
        if not self.spawn:
            raise RuntimeError(f"Map missing spawn position")
        self.follow_positions = data["pos"]
        self.oxygen_positions = data["oxygen"]
        
        self.floor = {}
        self.height = {}
        
        self.min_x, self.max_x = 0, 0
        self.min_y, self.max_y = 0, 0
        
        for pos, block in data["floor"].items():
            x, y = pos.split(";")
            x, y = eval(x), eval(y)
            pos = (x, y)
            
            self.floor[pos] = block
            
            if pos[0] < self.min_x:
                self.min_x = pos[0]
            if pos[0] > self.max_x:
                self.max_x = pos[0]
                
            if pos[1] < self.min_y:
                self.min_y = pos[1]
            if pos[1] > self.max_y:
                self.max_y = pos[1]
            
        for pos, block in data["height"].items():
            x, y = pos.split(";")
            x, y = eval(x), eval(y)
            pos = (x, y)
                        
            self.height[pos] = block
            
    def has_tile(self, pos):
        return pos in self.floor or pos in self.height
    
    def tile_data(self, pos):
        if pos in self.floor:
            return LOAD_NAMES[self.floor[pos]], False, self.floor[pos]
        else:
            name = LOAD_NAMES[self.height[pos]]
            if (pos[0], pos[1]-1) not in self.height:
                tex_name = TILES_SIDE[name] if name in TILES_SIDE else name
            else:
                tex_name = name
            return tex_name, True, self.height[pos]
        