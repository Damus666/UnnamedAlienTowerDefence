from .engine.prelude import *
import random

from .consts import *
from .attack import ATTACK_CLASSES, TreeAttack
from .ui import ProgressBar, image as ui_image
from . import god

class Tree:
    def __init__(self, tree: TreeData, pos):
        self.tree = tree
        self.grown = False
        self.size_mul = 0.5
        self.start_time = camera.get_ticks()
        self.rect = pygame.FRect(0, 0, tree.size, tree.size)
        self.rect.center = pos
        self.pos = pygame.Vector2(pos)
        self.energy = self.tree.energy*2
        self.rect_obj = RectObj(pos, None, (tree.size*self.size_mul, tree.size*self.size_mul), None, 
                                WORLD_ATLAS, god.assets.get_uvs(self.tree.tex_name))
        
        self.attacker: TreeAttack = ATTACK_CLASSES[self.tree.attack_mode](self)
        
        self.progress_bar = ProgressBar((self.rect.w*WORLD_BAR_XMUL, WORLD_BAR_H), WORLD_BAR_C, 1, None, COOLDOWN_BAR_FILL, COOLDOWN_BAR_BG, DARK_OUTLINE, outline="m",
                                        center=(self.rect.centerx, self.rect.bottom+WORLD_BAR_H))
        self.energy_bar = ProgressBar((self.rect.w*WORLD_BAR_XMUL, WORLD_BAR_H), WORLD_BAR_C, self.tree.energy, None, ENERGY_BAR_FILL, ENERGY_BAR_BG, DARK_OUTLINE, outline="m",
                                      center=(self.rect.centerx, self.rect.bottom+WORLD_BAR_H*2.5))
        self.warning_rect_objs = ui_image(None, (1, 1), "warning", None, self.rect.center)
        god.sounds.play("tree_place")
        
        god.settings.tutorial.placed_plant()
                
    def destroy(self):
        god.world.remove_tree(self)
        god.world.refresh_tree_lights()
        if god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range()
        
    def consume_energy(self):
        self.energy -= self.tree.energy_price
        if self.energy <= 0:
            self.energy = 0
            
    def restore_energy(self, amount):
        self.energy += amount
        if self.energy > self.tree.energy:
            self.energy = self.tree.energy
            god.player.add_xp(self.tree.place_xp/20)
        
    def get_bar_rect_objs(self):
        if self.energy != self.energy_bar.val:
            self.energy_bar.set_value(min(self.energy, self.tree.energy))
        if not self.grown:
            self.progress_bar.set_value(self.size_mul-0.5, 1-0.5)
        else:
            val = min(self.tree.attack_cooldown,((camera.get_ticks()-self.attacker.last_attack)/1000))
            if self.progress_bar.val != val:
                self.progress_bar.set_value(val, self.tree.attack_cooldown)
                
        return self.progress_bar.get_rect_objs()+self.energy_bar.get_rect_objs()
        
    def update_rect_obj(self):
        self.rect_obj.update_positions(self.rect.center, None, (self.tree.size*self.size_mul, self.tree.size*self.size_mul))
        god.world.refresh_building_like()
        
    def finish_growing(self):
        self.grown = True
        self.size_mul = 1
        god.player.add_xp(self.tree.place_xp/5)
        self.update_rect_obj()
        god.sounds.play("upgrade")
        if self.tree.has_light:
            god.world.refresh_tree_lights()
            #self.light = Light(self.rect.center, *self.tree.light_data)
            #self.world.add_static_light(self.light)
    
    def update(self):
        if not self.grown:
            grow_progress = (((camera.get_ticks()-self.start_time))/(self.tree.grow_time*1000))/2
            prev = self.size_mul
            self.size_mul = 0.5+grow_progress
            if round(self.size_mul, 1) != round(prev, 1):
                self.update_rect_obj()
            if self.size_mul >= 1:
                self.finish_growing()
        self.attacker.update()
            