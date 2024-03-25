from .engine.prelude import *
import pygame
import typing
if typing.TYPE_CHECKING:
    from .world import World

from .consts import *
from .tree import Tree
from .building import BUILDING_CLASSES

class Player:
    def __init__(self, world: "World"):
        self.pos = pygame.Vector2()
        self.speed = PLAYER_SPEED
        self.tool_idx = PICAXE_IDX
        self.energy = PLAYER_MAX_ENERGY
        self.xp = 0
        self.level = 10
        self.next_level_xp = NEXT_LEVEL_START_XP
        self.money = PLAYER_START_MONEY
        
        self.world = world
        
        self.status = "idle"
        self.y_status = "down"
        self.x_status = "left"
        self.seed_planting: TreeData = None
        self.building: BuildingData = None
                
        self.rect = pygame.FRect(0,0, OBJ_SIZE, OBJ_SIZE)
        self.hitbox = pygame.FRect(0,0,OBJ_SIZE/1.4, OBJ_SIZE/4)
        
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
        self.world.add_dynamic_light(self.light)
        
        self.unlit_rect_objs = [
            RectObj.null(), # block
            RectObj.null(), # destroy
            RectObj.null(), # preview,
            RectObj.null(), 
        ]
        self.unlit_batch = FixedRectsBatch(self.unlit_rect_objs, True).create_vao(REPLACE_SHADER, *SHADER_UNIFORMS)
        
    def seed_unlocked(self, seed: TreeData):
        return self.level >= seed.unlock_level
    
    def can_buy_seed(self, seed: TreeData):
        return self.seed_unlocked(seed) and self.can_buy(seed.price)
    
    def add_xp(self, amount):
        self.xp += amount
        if self.xp >= self.next_level_xp:
            self.xp = self.xp-self.next_level_xp
            self.level += 1
            self.next_level_xp *= NEXT_LEVEL_XP_MUL
            
    def add_money(self, amount):
        self.money += amount
        
    def can_buy(self, money):
        return self.money >= money
    
    def buy(self, money):
        self.money -= money
        if self.money < 0:
            self.money = 0
            
    def start_planting(self, seed: TreeData):
        self.stop_building()
        self.seed_planting = seed
        
    def plant(self, pos):
        tree = Tree(self.world, self.seed_planting, pos)
        self.world.add_tree(tree)
        self.buy(self.seed_planting.price)
        self.add_xp(self.seed_planting.plant_xp)
        if not self.can_buy_seed(self.seed_planting):
            self.stop_planting()
        
    def stop_planting(self):
        self.seed_planting = None
        self.unlit_rect_objs[P_PREVIEW_I] = RectObj.null()
        self.unlit_rect_objs[P_RANGEPREV_I] = RectObj.null()
        self.unlit_batch.update_rects(self.unlit_rect_objs)
        
    def start_building(self, building: BuildingData):
        self.stop_planting()
        self.building = building
        
    def stop_building(self):
        self.building = None
        self.unlit_rect_objs[P_PREVIEW_I] = RectObj.null()
        self.unlit_batch.update_rects(self.unlit_rect_objs)
        
    def build(self, pos):
        building = BUILDING_CLASSES[self.building.name](self.world, self.building, pos)
        self.world.add_building(building)
        self.buy(self.building.price)
        self.add_xp(self.building.buy_xp)
        if not self.can_buy(self.building.price):
            self.stop_planting()
    
    def update(self):
        keys = pygame.key.get_pressed()
        dir = pygame.Vector2()
        
        if keys[pygame.K_a]:
            dir.x -= 1
            self.x_status = "left"
        if keys[pygame.K_d]:
            dir.x += 1
            self.x_status = "right"
        if keys[pygame.K_w]:
            dir.y -= 1
            self.y_status = "up"
        if keys[pygame.K_s]:
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
            tile = self.world.get_tile(tile_center)
            if tile is not None:
                tile_center = tile.rect.center
            ok = self.world.can_build(self.seed_planting, tile_center, only_grassy=True)
            self.unlit_rect_objs[P_PREVIEW_I] = RectObj(tile_center, None, (self.seed_planting.size, self.seed_planting.size), 
                                              TREE_OK_COL if ok else TREE_BAD_COL, WORLD_ATLAS,
                                              self.world.assets.get_uvs(self.seed_planting.tex_name))
            self.unlit_rect_objs[P_RANGEPREV_I] = RectObj(tile_center, None, (self.seed_planting.attack_range*2, self.seed_planting.attack_range*2),
                                                PREVIW_RANGE_COL, WORLD_ATLAS, self.world.assets.get_uvs("circle_o"))
            self.unlit_batch.update_rects(self.unlit_rect_objs)
            
        if self.building is not None:
            tile_center = ((camera.world_mouse[0]), (camera.world_mouse[1]))
            tile = self.world.get_tile(tile_center)
            if tile is not None:
                tile_center = tile.rect.center
            ok = self.world.can_build(self.building, tile_center,
                    self.building.only_ore, self.building.only_grass, self.building.only_oxygen, self.building.is_bot, self.building.need_energy)
            self.unlit_rect_objs[P_PREVIEW_I] = RectObj(tile_center, None, (self.building.size, self.building.size),
                                              BUILDING_OK_COL if ok else BUILDING_BAD_COL, WORLD_ATLAS,
                                              self.world.assets.get_uvs(self.building.tex_name))
            self.unlit_batch.update_rects(self.unlit_rect_objs)
            
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
        colliding = self.hitbox.collidelistall(self.world.collision_rects)
        for other in colliding:
            other = self.world.collision_rects[other]
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
        colliding_down = self.hitbox.collidelist(self.world.jump_down_rects)
        if colliding_down > 0:
            colliding_down: pygame.FRect = self.world.jump_down_rects[colliding_down]
            if dir.y > 0:
                self.hitbox.top = colliding_down.bottom
                self.rect.bottom = self.hitbox.bottom
                self.pos.y = self.rect.centery
            else:
                self.hitbox.bottom = colliding_down.top
                self.rect.bottom = self.hitbox.bottom
                self.pos.y = self.rect.centery
            
        
    def event(self, event: pygame.Event):
        if event.type == pygame.MOUSEWHEEL:
            camera.mouse_wheel(event.y, ZOOM_MUL, ZOOM_MIN, ZOOM_MAX)
        if event.type == pygame.KEYDOWN:
            if event.unicode.isdecimal():
                idx = int(event.unicode)-1
                try:
                    self.start_planting(TreeData.get_all()[idx])
                except:
                    ...
            #if event.key == pygame.K_p:
            #    self.start_planting(TreeData.get("pepper"))
            if event.key == pygame.K_c:
                self.stop_planting()
                self.stop_building()
            #if event.key == pygame.K_s:
            #    self.start_building(BuildingData.get(ENERGY_SOURCE))
            #if event.key == pygame.K_d:
            #    self.start_building(BuildingData.get(ENERGY_DISTRIBUTOR))
            #if event.key == pygame.K_m:
            #    self.start_building(BuildingData.get(MINER))
            #if event.key == pygame.K_b:
            #    self.start_building(BuildingData.get(BOT))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            if self.seed_planting is not None:
                tile_center = ((camera.world_mouse[0]), (camera.world_mouse[1]))
                tile = self.world.get_tile(tile_center)
                if tile is not None:
                    tile_center = tile.rect.center
                if self.world.can_build(self.seed_planting, tile_center, only_grassy=True):
                    self.plant(tile_center)
            if self.building is not None:
                tile_center = ((camera.world_mouse[0]), (camera.world_mouse[1]))
                tile = self.world.get_tile(tile_center)
                if tile is not None:
                    tile_center = tile.rect.center
                if self.world.can_build(self.building, tile_center,
                    self.building.only_ore, self.building.only_grass, self.building.only_oxygen, self.building.is_bot, self.building.need_energy):
                    self.build(tile_center)
        
    def render(self):
        tex_array = self.world.assets["player"][self.status+(self.x_status if self.status == "runx" else self.y_status if self.status == "runy" else "")]
        tex_array.set_idx(self.cur_anim.get_idx())
        tex_array.use(0)
        self.rect_batch.render()
        self.world.assets.use()
        self.unlit_batch.render()
    