from .engine.prelude import *

from .consts import *
from .world_props import Tile

class Building:
    def __init__(self, world, building: BuildingData, pos):
        self.world, self.building = world, building
        self.rect = pygame.FRect(0, 0, building.size, building.size)
        self.rect.center = pos
        self.rect_obj = RectObj(pos, None, (building.size, building.size), None, 
                                WORLD_ATLAS, self.world.assets.get_uvs(building.tex_name))
        if building.has_light:
            self.light = Light(self.rect.center, *self.building.light_data)
            (self.world.add_static_light if not self.building.is_bot else self.world.add_dynamic_light)(self.light)

    def update(self):
        ...
        
class BotBuilding(Building):
    def __init__(self, *args):
        super().__init__(*args)
        self.working = False
        self.light.active = False
        
    
class MinerBuilding(Building):
    def __init__(self, *args):
        super().__init__(*args)
        self.ore_tile: Tile = self.world.get_floor_tile(self.rect.center)
        self.ore = TILES_ORES[self.ore_tile.tile_name]
        self.amount = 0
        self.mine_cooldown, self.stack_size = ORES_DATA[self.ore]
        self.last_mine = pygame.time.get_ticks()
        self.working = 1
        self.on_uvs, self.off_uvs = (self.world.assets.get_uvs(self.building.tex_name),
                                     self.world.assets.get_uvs(MINER_OFF))
        
    def update(self):
        if self.amount < self.stack_size:
            if self.working != True:
                self.working = True
                self.rect_obj.uv = self.on_uvs
                self.light.active = True
                self.world.update_buildings_batch()
            if pygame.time.get_ticks() - self.last_mine > self.mine_cooldown*1000:
                self.last_mine = pygame.time.get_ticks()
                self.amount += 1
        else:
            if self.working != False:
                self.working = False
                self.rect_obj.uv = self.off_uvs
                self.light.active = False
                self.world.update_buildings_batch()
        
        
BUILDING_CLASSES: list[str, type[Building]] = {
    ENERGY_SOURCE: Building,
    ENERGY_DISTRIBUTOR: Building,
    MINER: MinerBuilding,
    BOT: BotBuilding
}
        