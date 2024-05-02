from .engine.prelude import *
import pygame
import random

from .consts import *
from .tree import Tree
from .building import BUILDING_CLASSES
from .particle import MovingParticle
from .menu_ui import Indicator
from . import god

class Player:
    def __init__(self):
        god.player = self
        self.pos = pygame.Vector2()
        self.speed = PLAYER_SPEED
        self.tool_idx = PICAXE_IDX
        self.energy = PLAYER_MAX_ENERGY
        self.xp = 0
        self.level = 1
        self.next_level_xp = NEXT_LEVEL_START_XP
        self.money = PLAYER_START_MONEY
        self.inventory = list(PLAYER_INVENTORY)
                
        self.status = "idle"
        self.y_status = "down"
        self.x_status = "left"
        self.seed_planting: TreeData = None
        self.building: BuildingData = None
        self.level_up_time = -9999
        self.destroying = False
                
        self.rect = pygame.FRect(0,0, OBJ_SIZE, OBJ_SIZE)
        self.hitbox = pygame.FRect(0,0,OBJ_SIZE/1.4, OBJ_SIZE/4)
        self.dir = pygame.Vector2()
        
        self.anims = {
            "idledown": Anim(2, PLAYER_IDLE_SPEED),
            "idleup": Anim(2, PLAYER_IDLE_SPEED),
            "runxleft": Anim(6, PLAYER_RUN_SPEED),
            "runxright": Anim(6, PLAYER_RUN_SPEED),
            "runyup": Anim(6, PLAYER_RUN_SPEED),
            "runydown": Anim(6, PLAYER_RUN_SPEED)
        }
        self.cur_anim = self.anims["idledown"]
        
        self.rect_obj = RectObj(self.pos, None, [OBJ_SIZE, OBJ_SIZE], (1, 1, 1, 1), 0, None)
        self.rect_batch = FixedRectsBatch([self.rect_obj], True)
        self.rect_batch.create_vao(LIT_SHADER, *SHADER_UNIFORMS)
        
        self.light = Light(tuple(self.pos), PLAYER_LIGHT_COL, PLAYER_LIGHT_RANGE, PLAYER_LIGHT_INTENSITY)
        god.world.add_dynamic_light(self.light)
        
        self.unlit_rect_objs = [
            RectObj.null(), # block
            RectObj.null(), # destroy
            RectObj.null(), # preview,
            RectObj.null(), # rangeprev
        ]
        self.unlit_batch = FixedRectsBatch(self.unlit_rect_objs, True).create_vao(REPLACE_SHADER, *SHADER_UNIFORMS)
        
    def celebrate(self):
        if not god.settings.confetti:
            return
        for _ in range(350):
            pos = (self.pos.x+random.uniform(-20, 20), self.pos.y + random.uniform(-20, 20))
            size = random.uniform(0.08, 0.5)
            col = (random.random(), random.random(), random.random(), 1)
            dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            speed = random.uniform(5, 7)
            MovingParticle(pos, (size, size), dir, 15, speed, "circle", 0, col).instantiate()
        
    def seed_unlocked(self, seed: TreeData):
        return self.level >= seed.unlock_level
    
    def can_buy_seed(self, seed: TreeData):
        return self.seed_unlocked(seed) and self.can_buy(seed.price)
    
    def add_xp(self, amount):
        self.xp += amount
        Indicator("xp", amount)
        if self.xp >= self.next_level_xp:
            self.xp = self.xp-self.next_level_xp
            self.level += 1
            self.next_level_xp *= NEXT_LEVEL_XP_MUL
            self.level_up_time = camera.get_ticks()
            god.sounds.play("level_up")
            self.celebrate()
            god.world.ui.build()
        god.world.ui.update_static()
            
    def add_money(self, amount):
        self.money += amount
        Indicator("money", amount)
        god.world.ui.update_static()
        
    def can_buy(self, money):
        return self.money >= money
    
    def buy(self, money):
        self.money -= money
        if self.money < 0:
            self.money = 0
        god.world.ui.update_static()
            
    def start_planting(self, seed: TreeData):
        self.stop_building()
        if not god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range()
        self.seed_planting = seed
        
    def plant(self, pos):
        tree = Tree(self.seed_planting, pos)
        god.world.add_tree(tree)
        if tree.tree.name in self.inventory:
            self.inventory.remove(tree.tree.name)
        else:
            self.buy(self.seed_planting.price)
        self.add_xp(self.seed_planting.place_xp)
        if not self.can_buy_seed(self.seed_planting):
            self.stop_planting()
        if god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range(), god.world.ui.toggle_tree_range()
        
    def stop_planting(self):
        self.seed_planting = None
        self.unlit_rect_objs[P_PREVIEW_I] = RectObj.null()
        self.unlit_rect_objs[P_RANGEPREV_I] = RectObj.null()
        self.unlit_batch.update_rects(self.unlit_rect_objs)
        
    def start_building(self, building: BuildingData):
        self.stop_planting()
        if not god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range()
        self.building = building
        
    def stop_building(self):
        self.building = None
        self.unlit_rect_objs[P_PREVIEW_I] = RectObj.null()
        self.unlit_rect_objs[P_RANGEPREV_I] = RectObj.null()
        self.unlit_batch.update_rects(self.unlit_rect_objs)
        
    def build(self, pos):
        building = BUILDING_CLASSES[self.building.name](self.building, pos)
        god.world.add_building(building)
        god.world.refresh_buiding_energy()
        self.add_xp(self.building.place_xp)
        if not self.can_buy(self.building.price):
            self.stop_planting()
        if god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range(), god.world.ui.toggle_tree_range()
    
    def update(self):
        if god.world.ui.pause.is_open:
            return
        
        dir = pygame.Vector2()
        
        if god.settings.binds["left"].check_frame():
            dir.x -= 1
            self.x_status = "left"
        if god.settings.binds["right"].check_frame():
            dir.x += 1
            self.x_status = "right"
        if god.settings.binds["up"].check_frame():
            dir.y -= 1
            self.y_status = "up"
        if god.settings.binds["down"].check_frame():
            dir.y += 1
            self.y_status = "down"
        
        if dir.length() != 0:
            dir.normalize_ip()
            self.pos.x += dir.x*self.speed*camera.dt
            self.rect.centerx = self.pos.x
            self.hitbox.centerx = self.rect.centerx
            self.collisions("x", dir)
            self.pos.y += dir.y*self.speed*camera.dt
            self.rect.centery = self.pos.y
            self.hitbox.bottom = self.rect.bottom
            self.collisions("y", dir)
            
            self.update_buffer()
            
            if dir.x != 0:
                self.status = "runx"
            else:
                self.status = "runy"
        else:
            self.status = "idle"
            
        camera.position = self.pos.copy()
        if self.status == "idle":
            self.cur_anim = self.anims[self.status+self.y_status]
        else:
            self.cur_anim = self.anims[self.status+(self.x_status if self.status == "runx" else self.y_status)]
        self.cur_anim.update()
                
        if self.seed_planting is not None:
            tile_center = ((camera.world_mouse[0]), (camera.world_mouse[1]))
            tile = god.world.get_tile(tile_center)
            if tile is not None:
                tile_center = tile.rect.center
            ok = god.world.can_build(self.seed_planting, tile_center, only_grassy=True)
            self.unlit_rect_objs[P_PREVIEW_I] = RectObj(tile_center, None, (self.seed_planting.size, self.seed_planting.size), 
                                              TREE_OK_COL if ok else TREE_BAD_COL, WORLD_ATLAS,
                                              god.assets.get_uvs(self.seed_planting.tex_name))
            self.unlit_rect_objs[P_RANGEPREV_I] = RectObj(tile_center, None, (self.seed_planting.attack_range*2, self.seed_planting.attack_range*2),
                                                PREVIW_RANGE_COL, WORLD_ATLAS, god.assets.get_uvs("circle_o"))
            self.unlit_batch.update_rects(self.unlit_rect_objs)
            
        if self.building is not None:
            tile_center = ((camera.world_mouse[0]), (camera.world_mouse[1]))
            tile = god.world.get_tile(tile_center)
            if tile is not None:
                tile_center = tile.rect.center
            ok = god.world.can_build(self.building, tile_center,
                    self.building.only_ore, self.building.only_grass, self.building.only_oxygen, self.building.is_bot, self.building.need_energy)
            self.unlit_rect_objs[P_PREVIEW_I] = RectObj(tile_center, None, (self.building.size, self.building.size),
                                              BUILDING_OK_COL if ok else BUILDING_BAD_COL, WORLD_ATLAS,
                                              god.assets.get_uvs(self.building.tex_name))
            if self.building.tex_name in ENERGY_TILES:
                self.unlit_rect_objs[P_RANGEPREV_I] = RectObj(tile_center, None, (ENERGY_DISTANCE*2, ENERGY_DISTANCE*2),
                                                PREVIW_ENERGY_COL, WORLD_ATLAS, god.assets.get_uvs("circle_o"))
            self.unlit_batch.update_rects(self.unlit_rect_objs)
            
        if self.destroying:
            center = None
            size = 0
            for tree in reversed(god.world.trees):
                if tree.rect.collidepoint(camera.world_mouse):
                    center = tree.rect.center
                    size = tree.tree.size
                    break
            if center is None:
                for building in reversed(god.world.buildings):
                    if building.rect.collidepoint(camera.world_mouse):
                        center = building.rect.center
                        size = building.building.size
                        break
            if center is not None:
                self.unlit_rect_objs[P_DESTROY_I] = RectObj(center, None, (size*2, size*2), DESTROY_COLOR, WORLD_ATLAS, god.assets.get_uvs("circle"))
                self.unlit_batch.update_rects(self.unlit_rect_objs)
            else:
                self.unlit_rect_objs[P_DESTROY_I] = RectObj.null()
                self.unlit_batch.update_rects(self.unlit_rect_objs)
            
        self.dir = dir
            
    def update_buffer(self):
        self.rect_obj.update_positions(self.pos, None)
        self.rect_batch.update_rects()
        self.light.rect.center = tuple(self.pos)
        
    def teleport(self, pos):
        self.pos = pygame.Vector2(pos)
        self.rect.center = pos
        self.hitbox.midbottom = self.rect.midbottom
        self.update_buffer()
                        
    def collisions(self, axis, dir):
        colliding = self.hitbox.collidelistall(god.world.collision_rects)
        for other in colliding:
            other = god.world.collision_rects[other]
            if axis == "x":
                self.hitbox.right = other.left if dir.x > 0 else self.hitbox.right
                self.hitbox.left = other.right if dir.x < 0 else self.hitbox.left
                self.rect.centerx, self.pos.x = self.hitbox.centerx, self.hitbox.centerx
            else:
                self.hitbox.top = other.bottom if dir.y < 0 else self.hitbox.top
                self.hitbox.bottom = other.top if dir.y > 0 else self.hitbox.bottom
                self.rect.bottom = self.hitbox.bottom
                self.pos.y = self.rect.centery
                
    def jump_collisions(self, dir):
        colliding_down = self.hitbox.collidelist(god.world.jump_down_rects)
        if colliding_down > 0:
            colliding_down: pygame.FRect = god.world.jump_down_rects[colliding_down]
            if dir.y > 0:
                self.hitbox.top = colliding_down.bottom
                self.rect.bottom = self.hitbox.bottom
                self.pos.y = self.rect.centery
            else:
                self.hitbox.bottom = colliding_down.top
                self.rect.bottom = self.hitbox.bottom
                self.pos.y = self.rect.centery
                
    def stop_destroying(self):
        self.destroying = False
        self.unlit_rect_objs[P_DESTROY_I] = RectObj.null()
        self.unlit_batch.update_rects(self.unlit_rect_objs)
    
    def event_pause(self):
        self.stop_planting()
        self.stop_building()
        if god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range()
        god.world.ui.shop.close()
        self.stop_destroying()
        
        god.world.ui.pause.toggle()
        
    def event_range(self):
        god.world.ui.toggle_tree_range()
        
    def event_destroy(self):
        self.stop_planting()
        self.stop_building()
        god.world.ui.shop.close()
        
        self.destroying = not self.destroying
        if not self.destroying:
            self.stop_destroying()
        else:
            if god.world.ui.tree_range_active:
                god.world.ui.toggle_tree_range()
        
    def event_shop(self):
        god.world.ui.shop.toggle()
        self.stop_planting()
        self.stop_building()
        self.stop_destroying()
        if god.world.ui.tree_range_active:
            god.world.ui.toggle_tree_range()
            
    def event_start_wave(self):
        if not god.world.spawner.wave_active and god.settings.tutorial.complete:
            god.world.spawner.start_wave()
        
    def event(self, event: pygame.Event):
        if god.world.ui.pause.settings.listening:
            return
        
        if event.type == pygame.MOUSEWHEEL and event.y*camera.time_scale != 0:
            camera.mouse_wheel(event.y, ZOOM_MUL, ZOOM_MIN, ZOOM_MAX)
            
        if god.settings.binds["cancel_action"].check_event(event):
            done = self.seed_planting is not None or self.building is not None or god.world.ui.tree_range_active or god.world.ui.shop.is_open or self.destroying
            
            self.stop_planting()
            self.stop_building()
            if god.world.ui.tree_range_active:
                god.world.ui.toggle_tree_range()
            god.world.ui.shop.close()
            self.stop_destroying()
            
            if done:
                return
            
        if god.settings.binds["pause"].check_event(event):
            self.event_pause()
            return
            
        if god.settings.binds["tree_range"].check_event(event):
            self.event_range()
            return
        
        if god.settings.binds["destroy_mode"].check_event(event):
            self.event_destroy()
            return
        
        if god.settings.binds["start_wave"].check_event(event):
            self.event_start_wave()
            return
        
        if not god.world.ui.pause.is_open and god.settings.binds["shop"].check_event(event):
            self.event_shop()
            return
        
        if god.world.ui.pause.is_open or god.world.ui.overlay_rect.collidepoint(camera.ui_mouse):
            return
        
        if god.settings.binds["place"].check_event(event):
            if self.destroying:
                for tree in reversed(god.world.trees):
                    if tree.rect.collidepoint(camera.world_mouse):
                        tree.destroy()
                else:
                    for building in reversed(god.world.buildings):
                        if building.rect.collidepoint(camera.world_mouse):
                            building.destroy()
                return
            
            if self.seed_planting is not None:
                tile_center = ((camera.world_mouse[0]), (camera.world_mouse[1]))
                tile = god.world.get_tile(tile_center)
                if tile is not None:
                    tile_center = tile.rect.center
                if god.world.can_build(self.seed_planting, tile_center, only_grassy=True):
                    self.plant(tile_center)
                    return
                
            if self.building is not None:
                tile_center = ((camera.world_mouse[0]), (camera.world_mouse[1]))
                tile = god.world.get_tile(tile_center)
                if tile is not None:
                    tile_center = tile.rect.center
                if god.world.can_build(self.building, tile_center,
                    self.building.only_ore, self.building.only_grass, self.building.only_oxygen, self.building.is_bot, self.building.need_energy):
                    self.build(tile_center)
                    return
        
    def render(self):
        tex_array = god.assets.player[self.status+(self.x_status if self.status == "runx" else self.y_status if self.status == "runy" else "")]
        tex_array.set_idx(self.cur_anim.get_idx())
        tex_array.use(0)
        self.rect_batch.render()
        god.assets.use()
        
    def post_render(self):
        self.unlit_batch.render()
    