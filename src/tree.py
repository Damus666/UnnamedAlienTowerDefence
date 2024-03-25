from .engine.prelude import *
import random

from .consts import *
from .particle import Proj
from .attack import ATTACK_CLASSES, TreeAttack

class Tree:
    def __init__(self, world, tree: TreeData, pos):
        self.world, self.tree = world, tree
        self.grown = False
        self.size_mul = 0.5
        self.start_time = pygame.time.get_ticks()
        self.rect = pygame.FRect(0, 0, tree.size, tree.size)
        self.rect.center = pos
        self.pos = pygame.Vector2(pos)
        self.rect_obj = RectObj(pos, None, (tree.size*self.size_mul, tree.size*self.size_mul), None, 
                                WORLD_ATLAS, self.world.assets.get_uvs(self.tree.tex_name))
        self.attacker: TreeAttack = ATTACK_CLASSES[self.tree.attack_mode](self)
        
    def update_rect_obj(self):
        self.rect_obj.update_positions(self.rect.center, None, (self.tree.size*self.size_mul, self.tree.size*self.size_mul))
        self.world.update_buildings_batch()
        
    def finish_growing(self):
        self.grown = True
        self.size_mul = 1
        self.world.player.add_xp(self.tree.grow_xp)
        self.update_rect_obj()
        if self.tree.has_light:
            self.world.refresh_tree_lights()
            #self.light = Light(self.rect.center, *self.tree.light_data)
            #self.world.add_static_light(self.light)
    
    def update(self):
        if not self.grown:
            grow_progress = (((pygame.time.get_ticks()-self.start_time))/(self.tree.grow_time*1000))/2
            prev = self.size_mul
            self.size_mul = 0.5+grow_progress
            if round(self.size_mul, 1) != round(prev, 1):
                self.update_rect_obj()
            if self.size_mul >= 1:
                self.finish_growing()
            return
        self.attacker.update()
            