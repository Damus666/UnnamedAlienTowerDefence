import random
import noise
import json
import typing
if typing.TYPE_CHECKING:
    from .world import World

from .consts import *
from .enemy import Enemy
from .particle import MovingParticle

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
    def __init__(self, world: "World", topleft, size, tile_name, is_floor=False, is_plant=False, is_ore=False, rect_obj=None):
        self.world, self.tile_name, self.is_floor, self.is_plant, self.is_height, self.is_ore = world, tile_name, is_floor, is_plant, not is_floor, is_ore
        self.topleft = pygame.Vector2(topleft)
        self.rect = pygame.FRect(self.topleft, (size, size))
        self.rect_obj = rect_obj
        
class BubbleSpawner:
    def __init__(self, world: "World", pos):
        self.world = world
        self.pos = (pos[0], pos[1]-0.11)
        self.last_bubble = pygame.time.get_ticks()
        
    def update(self):
        if pygame.time.get_ticks()-self.last_bubble > 0.15*1000:
            self.last_bubble = pygame.time.get_ticks()
            dir = (random.uniform(-0.19, 0.19), -1)
            size = (random.uniform(0.11, 0.31))
            self.world.add_uparticle(MovingParticle(self.world, self.pos, (size, size), dir, 3.5, random.uniform(0.8, 1.2), "bubble"))
        
class EnemyWaveSpawner:
    def __init__(self, world: "World"):
        self.world = world
        self.map = self.world.map
        self.waves_amount = len(self.world.map.waves)
        self.wave_stages = self.world.map.waves[0]
        self.current_stage = self.wave_stages[0]
        self.stage_idx = 0
        self.stages_amount = len(self.wave_stages)
        self.wave_idx = 0
        self.wave_active = False
        self.wave_end_time = pygame.time.get_ticks()
        self.map_complete = False
        self.spawned_emenies = 0
        self.killed_enemies = 0
        self.stage_active = True
        self.stage_end_time = pygame.time.get_ticks()
        self.stages_completed = False
        self.stage_spanwed_enemies = 0
        self.last_enemy = 0
        
    def update(self):
        if self.map_complete:
            return
        if not self.wave_active:
            if pygame.time.get_ticks() - self.wave_end_time > WAVE_COOLDOWN*1000:
                self.start_wave()
        else:
            if not self.stages_completed:
                if self.stage_active:
                    if self.stage_spanwed_enemies < self.current_stage["enemy_amount"]:
                        if pygame.time.get_ticks() - self.last_enemy > self.current_stage["spawn_cooldown"]*1000:
                            self.spawn_enemy()
                    else:
                        self.end_stage()
                else:
                    if pygame.time.get_ticks() - self.stage_end_time > self.current_stage["wait_time"]*1000:
                        self.start_stage()
            if self.spawned_emenies > 0 and self.killed_enemies == self.spawned_emenies:
                self.end_wave()
                
    def spawn_enemy(self):
        self.last_enemy = pygame.time.get_ticks()
        enemy = Enemy(self.world, EnemyData.get(self.current_stage["enemy_name"]), self.world.portal_tile.rect.center)
        self.world.add_enemy(enemy)
        self.spawned_emenies += 1
        self.stage_spanwed_enemies += 1
        
    def enemy_destroyed(self):
        self.killed_enemies += 1
                
    def end_stage(self):
        self.stage_idx += 1
        if self.stage_idx >= self.stages_amount:
            self.stages_completed = True
            return
        self.current_stage = self.wave_stages[self.stage_idx]
        self.stage_active = False
        self.stage_end_time = pygame.time.get_ticks()
        
    def start_stage(self):
        self.stage_active = True
        self.stage_spanwed_enemies = 0
        self.last_enemy = pygame.time.get_ticks()
                
    def start_wave(self):
        self.wave_active = True
        self.stage_active = True
        
    def end_wave(self):
        self.wave_idx += 1
        if self.wave_idx >= self.waves_amount:
            self.map_complete = True
            return
        self.wave_stages = self.world.map.waves[self.wave_idx]
        self.wave_active = False
        self.wave_end_time = pygame.time.get_ticks()
        self.current_stage = self.wave_stages[0]
        self.stage_idx = 0
        self.stages_amount = len(self.wave_stages)
        self.stages_completed = False
        self.spawned_emenies = 0
        self.killed_enemies = 0
        
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