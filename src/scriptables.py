from .engine.prelude import *
from typing import TypedDict

class TreeProj(TypedDict):
    speed: float
    size: list[float]
    tex_name: str
    dist: float
    color: list[float]
    inflate: float
    offset: float
    damage: float
    
class TreeArea(TypedDict):
    radius: float
    tex_name: str
    grow_time: float
    damage: float
    color: list[float]
    disappear_time: float
    y: bool
    x: float
    
class TreeBurst(TypedDict):
    cooldown: float
    amount: int
    
class TreeEffect(TypedDict):
    name: str
    ticks: int
    damage: float
    speed_mul: float
    
class TreeSequence(TypedDict):
    amount: 3
    
class TreeBeam(TypedDict):
    color: list[float]
    tex_name: str
    size: float
    ticks: float
    damage: float
    
class TreeData(Scriptable):
    has_light = False
    light_data: list[list[float], float]

    tex_name: str
    size = 2
    grow_time: int
    unlock_level: int
    price: int
    plant_xp = 0
    grow_xp = 0
    
    attack_range: float
    attack_cooldown: float
    attack_mode: str
    proj: TreeProj
    burst: TreeBurst
    split: TreeProj
    area: TreeArea
    effect: TreeEffect
    has_effect = False
    sequence: TreeSequence
    beam: TreeBeam
    
    def init(self):
        if self.optional("tex_name"):
            self.tex_name = self.name
        if hasattr(self, "effect"):
            self.has_effect = True
        if hasattr(self, "proj"):
            self.proj["dist"] = self.attack_range*1.5
            
class EnemyData(Scriptable):
    has_light = False
    light_data: list[list[float], float]
    
    tex_name: str
    
    size = 1.1
    speed: float
    health: float
    reward: float
    reward_mul: float = 1
    
    buff: str
    has_buff = False
    
    def init(self):
        if self.optional("tex_name"):
            self.tex_name = self.name
        if hasattr(self, "buff"):
            self.has_buff = True
        self.reward = self.health*self.reward_mul

ENERGY_SOURCE = "energy_source"
ENERGY_DISTRIBUTOR = "energy_distributor"
MINER = "miner"
BOT = "bot"
              
class BuildingData(Scriptable):
    has_light = False
    light_data: list[list[float], float]
    
    size: int
    price: int
    
    only_oxygen: bool = False
    only_ore: bool = False
    only_grass: bool = False
    is_bot: bool = False
    need_energy: bool = False
        
    tex_name: str
    
    buy_xp: int
    place_xp: int
    
    def init(self):
        if self.optional("tex_name"):
            self.tex_name = self.name
        if self.name == BOT:
            self.is_bot = True
        elif self.name == MINER:
            self.only_ore = True
            self.need_energy = True
        elif self.name == ENERGY_SOURCE:
            self.only_oxygen = True
        elif self.name == ENERGY_DISTRIBUTOR:
            self.need_energy = True
            
class MapWaveStage(TypedDict):
    wait_time: float
    enemy_name: str
    enemy_amount: int
    spawn_cooldown: float
                
class MapData(Scriptable):
    data_path: str
    index: int
    health: float
    
    waves: list[list[MapWaveStage]]
    
    def init(self):
       self.data_path = f"assets/maps/{self.index}.json" 
    