from .engine.prelude import *
import random
import math

from .consts import *
from .world_props import Tile
from .ui import ProgressBar
from .tree import Tree
from .particle import Particle
from . import ui
from . import god

class Building:
    def __init__(self, building: BuildingData, pos):
        self.building = building
        self.rect = pygame.FRect(0, 0, building.size, building.size)
        self.rect.center = pos
        self.rect_obj = RectObj(pos, None, (building.size, building.size), None, 
                                WORLD_ATLAS, god.assets.get_uvs(building.tex_name))
        self.pos = pygame.Vector2(pos)
        
        if self.building.name in god.player.inventory:
            god.player.inventory.remove(self.building.name)
            god.world.ui.update_static()
        else:
            god.player.buy(self.building.price)
        
        god.settings.tutorial.placed_building(self.building.name)
        
        if building.has_light:
            self.light = Light(self.rect.center, *self.building.light_data)
            (god.world.add_static_light if not self.building.is_bot else god.world.add_dynamic_light)(self.light)

        god.sounds.play_random("building_place")
        
    def destroy(self):
        if self.building.name in PLAYER_INVENTORY and not self.building.name in god.player.inventory:
            god.player.inventory.append(self.building.name)
            god.world.ui.update_static()
            
        god.world.remove_building(self)
        
        if self.building.has_light:
            (god.world.remove_static_light if not self.building.is_bot else god.world.remove_dynamic_light)(self.light)
        if god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range()
        god.world.refresh_buiding_energy()
        
    def update(self):
        ...
        
    def update_rect_obj(self):
        #if self.rect.colliderect(camera.world_rect):
        self.rect_obj.update_positions(self.rect.center, None, self.rect.size)
        if not self.building.is_bot:
            god.world.refresh_building_like()
        if self.building.has_light:
            self.light.rect.center = self.rect.center
        
    def get_ui_rect_objs(self):
        return []
        
class BotBuilding(Building):
    def __init__(self, *args):
        super().__init__(*args)
        
        self.right_uvs = god.assets.get_uvs(self.building.tex_name)
        self.left_uvs = god.assets.get_uvs(self.building.tex_name, flipx=True)
        
        self.ore = None
        self.amount = 0
        self.target = None
        self.next_target = None
        
        self.last_particle = 0
        self.stop_pos = None
        self.offset = random.random()*200
        
    def get_ui_rect_objs(self):
        if self.ore is not None:
            sizeb, size = 0.6, 0.5
            return (
                ui.image(None, (sizeb, sizeb), "circle", (1, 1, 1, 0.3), center=(self.rect.centerx, self.rect.bottom+S+sizeb/2))
                +ui.image(None, (size, size), self.ore, center=(self.rect.centerx, self.rect.bottom+S+sizeb/2))
            )
        return []
        
    def tree_contact(self):
        self.target: Tree
        while self.target.energy < self.target.tree.energy and self.amount > 0:
            self.amount -= 1
            self.target.restore_energy(ORES_DATA[self.ore][2])
        if self.amount <= 0:
            self.ore = None
        self.target = None
        self.next_target = None
        
    def miner_contact(self):
        self.target: MinerBuilding
        if self.target.amount > 0:
            if self.rect.colliderect(camera.world_rect):
                god.sounds.play("ore")
            self.amount = self.target.amount
            self.target.amount = 0
            self.target.refresh_amount()
            self.ore = self.target.ore
            self.target = self.next_target
            self.next_target = None
        
    def update(self):
        self.light.active = False
        if self.target is None and self.next_target is None:
            for tree in sorted(god.world.trees, key=lambda t: t.pos.distance_to(self.rect.center)):
                if tree.energy < tree.tree.energy:
                    if self.amount <= 0:
                        self.next_target = tree
                        self.target = None
                    else:
                        self.next_target = None
                        self.target = tree
                    break
                    
        if self.next_target is not None and self.target is None:
            for miner in sorted(god.world.miner_buildings, key=lambda m: m.pos.distance_to(self.rect.center)):
                if miner.amount > 0:
                    self.target = miner
                    break
                
        if self.target is not None:
            if not self.rect.colliderect(self.target.rect):
                self.stop_pos = None
                dir = (self.target.pos-self.pos).normalize()
                self.pos += dir*camera.dt*BOT_SPEED
                self.rect.center = self.pos
                if self.pos.x-self.target.pos.x < 0:
                    self.rect_obj.uv = self.left_uvs
                else:
                    self.rect_obj.uv = self.right_uvs
                self.update_rect_obj()
                if camera.get_ticks() - self.last_particle >= 0.2*1000:
                    self.last_particle = camera.get_ticks()
                    size = (random.uniform(0.11, 0.31))
                    Particle(self.pos, (size, size), "bubble", duration=1).instantiate()
                self.light.active = True
            else:
                self.update_rect_obj()
                if isinstance(self.target, MinerBuilding):
                    self.miner_contact()
                else:
                    self.tree_contact()
        else:
            if self.stop_pos is None:
                self.stop_pos = self.pos.copy()
            self.pos = self.stop_pos + pygame.Vector2(0, math.sin((camera.get_ticks()+self.offset)*0.006)*0.3)
            self.rect.center = self.pos
            self.update_rect_obj()
    
    
class MinerBuilding(Building):
    def __init__(self, *args):
        super().__init__(*args)
        self.ore_tile: Tile = god.world.get_floor_tile(self.rect.center)
        self.ore = TILES_ORES[self.ore_tile.tile_name]
        self.amount = 0
        self.mine_cooldown, self.stack_size, *_ = ORES_DATA[self.ore]
        self.last_mine = camera.get_ticks()
        self.working = True
        self.can_work = True
        self.on_uvs, self.off_uvs = (god.assets.get_uvs(self.building.tex_name),
                                     god.assets.get_uvs(MINER_OFF))
        
        self.progress_bar = ProgressBar((self.rect.w*WORLD_BAR_XMUL, WORLD_BAR_H), WORLD_BAR_C, self.mine_cooldown, None, COOLDOWN_BAR_FILL, COOLDOWN_BAR_BG, DARK_OUTLINE, outline="m",
                                        center=(self.rect.centerx, self.rect.bottom+WORLD_BAR_H))
        size, sizeb = 0.6, 0.9
        self.sizeb = sizeb
        self.ore_img_rects = ui.image(None, (size, size), self.ore, center=(self.rect.centerx-sizeb/2, self.rect.top-S-sizeb/2))
        self.bgcircle_img_rects = ui.image((self.rect.centerx-sizeb, self.rect.top-S-sizeb), (sizeb, sizeb), "circle", (1, 1, 1, 0.3))
        self.refresh_amount()
        pygame.Vector2().as_polar()
        
    def get_ui_rect_objs(self):
        self.progress_bar.set_value(min(self.mine_cooldown, (camera.get_ticks()-self.last_mine)/1000))
        return (self.progress_bar.get_rect_objs()
                +self.bgcircle_img_rects
                +self.ore_img_rects
                +self.amount_rects)
        
    def refresh_amount(self):
        self.amount_rects = font.render_single(MAIN_FONT, f"{self.amount}/{self.stack_size}", (self.rect.centerx+S, self.rect.top-S-self.sizeb/2),
                                                       1.5, "ml")
        
    def disable_working(self):
        self.working = False
        self.can_work = False
        self.rect_obj.uv = self.off_uvs
        self.light.active = False
        self.update_rect_obj()
        god.world.refresh_building_like()
        
    def enable_working(self):
        self.can_work = True
        self.working = False
        
    def update(self):
        if not self.can_work:
            return
        if self.amount < self.stack_size:
            if self.working != True:
                self.working = True
                self.rect_obj.uv = self.on_uvs
                self.light.active = True
                self.update_rect_obj()
                god.world.refresh_building_like()
            if camera.get_ticks() - self.last_mine > self.mine_cooldown*1000:
                self.last_mine = camera.get_ticks()
                self.amount += 1
                self.refresh_amount()
        else:
            if self.working != False:
                self.working = False
                self.rect_obj.uv = self.off_uvs
                self.light.active = False
                self.update_rect_obj()
                god.world.refresh_building_like()
        
        
BUILDING_CLASSES: list[str, type[Building]] = {
    ENERGY_SOURCE: Building,
    ENERGY_DISTRIBUTOR: Building,
    MINER: MinerBuilding,
    BOT: BotBuilding
}
        