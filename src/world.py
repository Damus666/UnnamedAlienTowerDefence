from .engine.prelude import *
import random

from .consts import *
from .player import Player
from .world_props import PlantNoiseSettings, NoiseSettings, MapLoader, Tile, EnemyWaveSpawner, BubbleSpawner
from .tree import Tree
from .enemy import Enemy
from .building import Building, BotBuilding
from .assets import Assets

class World(Scene):
    grass_plant_noise = PlantNoiseSettings(-0.5, GRASS_PLANT_TILE)
    spiral_noise = PlantNoiseSettings(-0.6, SPIRAL_TILE)
    cactus_noise = PlantNoiseSettings(-0.67, CACTUS_TILE)
    flowers_noise = PlantNoiseSettings(-0.67, FLOWERS_TILE)
    spores_noise = PlantNoiseSettings(-0.65, SPORES_TILE)
    rove_noise = NoiseSettings(ROVE_OCTAVES, ROVE_SCALE, -0.62, ROVE_TILE)
    
    def init(self, map: MapData):
        self.map = map
        self.assets: Assets = self.manager.assets
        self.health = self.map.health
        self.map_loader = MapLoader(self.map)
        self.spawner = EnemyWaveSpawner(self)
        self.silly_obj = [RectObj((1, 1), None, (0.001, 0.001), None, 2, None)]
        
        self.floor_tiles: list[Tile] = {}
        self.height_tiles: list[Tile] = {}
        self.plant_tiles: list[Tile] = []
        self.oxygen_tiles: list[Tile] = []
        self.can_be_above: list[Tile] = []
        self.can_be_above_unlit: list[Tile] = []
        
        self.dust_rect_objs, self.tile_rect_objs, self.plant_rect_objs = [], [], []
        self.jump_up_rects, self.jump_down_rects = [], []
        self.collision_rects = self.map_loader.collisions
        self.bubble_spawners = []
        self.static_light_batch, self.dynamic_light_batch = LightBatch(self.light_filter), LightBatch(self.light_filter)
        
        self.trees: list[Tree] = []
        self.buildings: list[Building] = []
        self.energy_buildings: list[Building] = []
        self.miner_buildings: list[Building] = []
        self.buildings_rect_objs = []
        self.tree_lights: list[Light] = []
        self.buildings_batch = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        
        self.enemies: list[Enemy] = []
        self.bots: list[BotBuilding] = []
        self.bots_rect_objs = []
        self.bots_batch = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        self.enemies_shot = []
        
        self.uparticles = []
        self.uparticles_rect_objs = []
        self.uparticles_batch = GrowingRectsBatch(UNLIT_SHADER, *SHADER_UNIFORMS)
        
        self.build_asteroid()      
        self.add_spawner()
        self.add_oxygens()
        self.add_light_to_plants()
        
        self.follow_pos = [pygame.Vector2(sp) for sp in sorted(self.map_loader.follow_positions,
                                                               key = lambda pos: pos[1])]
        self.follow_rects = [pygame.FRect(sp.x, sp.y, 0.2, 0.2) for sp in self.follow_pos]
        
        self.above_batch = FixedRectsBatch([], True, MAX_CAN_BE_ABOVE).create_vao(LIT_SHADER, *SHADER_UNIFORMS)
        self.above_unlit_batch = FixedRectsBatch([], True, MAX_CAN_BE_ABOVE).create_vao(UNLIT_SHADER, *SHADER_UNIFORMS)
        self.dust_rects_batch = FixedRectsBatch(self.dust_rect_objs, False).create_vao(UNLIT_SHADER, *SHADER_UNIFORMS)
        self.tile_rects_batch = FixedRectsBatch(self.tile_rect_objs+self.plant_rect_objs, False).create_vao(LIT_SHADER, *SHADER_UNIFORMS)
        self.random_unlit_batch = FixedRectsBatch([self.portal_tile.rect_obj], True).create_vao(UNLIT_SHADER, *SHADER_UNIFORMS)
                
        self.player = Player(self)
        self.free_buffers()
        self.portal_angle = 0
        
    def boss_spawned(self):
        self.random_unlit_batch.rect_objs.remove(self.portal_tile.rect_obj)
        self.random_unlit_batch.update_rects()
        self.tile_rects_batch.rect_objs.remove(self.portalframe_tile.rect_obj)
        self.tile_rects_batch.update_rects()
        self.tile_rects_batch.free_rect_objs()
        self.remove_static_light(self.spawner_light)
        
    def damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            print("Game over lmao")
            self.manager.quit()
            
    def add_uparticle(self, particle):
        self.uparticles.append(particle)
        self.uparticles_rect_objs = [p.rect_obj for p in self.uparticles]+self.silly_obj
        self.uparticles_batch.update_rects(self.uparticles_rect_objs)
        
    def remove_uparticle(self, particle):
        self.uparticles.remove(particle)
        self.uparticles_rect_objs = [p.rect_obj for p in self.uparticles]+self.silly_obj
        self.uparticles_batch.update_rects(self.uparticles_rect_objs)
        
    def add_tree(self, tree: Tree):
        self.trees.append(tree)
        self.add_building_like(tree)
        
    def remove_tree(self, tree: Tree):
        self.trees.remove(tree)
        self.remove_building_like(tree)
        
    def add_enemy(self, enemy: Enemy):
        self.enemies.append(enemy)
        self.add_bot_like(enemy)
        
    def remove_enemy(self, enemy: Enemy):
        self.enemies.remove(enemy)
        self.remove_bot_like(enemy)
        
    def add_building(self, building: Building):
        self.buildings.append(building)
        if building.building.is_bot:
            self.bots.append(building)
            self.add_bot_like(building)
            return
        if building.building.name in [ENERGY_SOURCE, ENERGY_DISTRIBUTOR]:
            self.energy_buildings.append(building)
        elif building.building.name in [MINER]:
            self.miner_buildings.append(building)
        self.add_building_like(building)
        
    def remove_building(self, building: Building):
        self.buildings.remove(building)
        if building.building.is_bot:
            self.bots.remove(building)
            self.remove_bot_like(building)
            return
        if building.building.name in [ENERGY_SOURCE, ENERGY_DISTRIBUTOR]:
            self.energy_buildings.remove(building)
        elif building.building.name in [MINER]:
            self.miner_buildings.remove(building)
        self.remove_building_like(building)
        
    def add_bot_like(self, bot):
        self.can_be_above.append(bot)
        self.refresh_bot_like()
        
    def remove_bot_like(self, bot):
        self.can_be_above.remove(bot)
        self.refresh_bot_like()
        
    def refresh_bot_like(self):
        self.sort()
        self.bots_rect_objs = [enemy.rect_obj for enemy in self.enemies+self.bots]+self.silly_obj
        self.update_bots_batch()
        
    def add_building_like(self, building):
        self.can_be_above.append(building)
        self.refresh_building_like()
        
    def remove_building_like(self, building):
        self.can_be_above.remove(building)
        self.refresh_building_like()
        
    def refresh_building_like(self):
        self.sort()
        self.buildings_rect_objs = [tree.rect_obj for tree in self.trees+self.buildings]
        self.update_buildings_batch()
    
    def update_bots_batch(self):
        self.bots_batch.update_rects(self.bots_rect_objs)
        
    def update_buildings_batch(self):
        self.buildings_batch.update_rects(self.buildings_rect_objs)
        self.buildings_batch.free_rect_objs()
        
    def sort(self):
        self.trees.sort(key=lambda tree: tree.rect.centery)
        self.enemies.sort(key=lambda enemy: enemy.rect.center)
        self.can_be_above.sort(key=lambda obj: obj.rect.centery)
        
    def add_spawner(self):
        self.portal_tile = Tile(self, (self.map_loader.spawn[0]-SPAWNER_SIZE/4, self.map_loader.spawn[1]-SPAWNER_SIZE/4), SPAWNER_SIZE, SPAWNER_TILE, is_plant=True)
        rect_obj=RectObj(self.portal_tile.rect.center, None, self.portal_tile.rect.size, PORTAL_COL, 
                                            WORLD_ATLAS, self.assets.get_uvs(SPAWNER_TILE))
        self.portal_tile.rect_obj = rect_obj
        self.can_be_above_unlit.append(self.portal_tile)
        self.spawner_light = Light(self.portal_tile.rect.center, *SPAWNER_LIGHT_DATA)
        self.add_static_light(self.spawner_light)
        
        self.portalframe_tile = Tile(self, (0, 0), SPAWNER_SIZE*1.1, PORTALFRAME_TILE)
        self.portalframe_tile.rect.center = (self.portal_tile.rect.centerx, self.portal_tile.rect.centery+0.17)
        self.plant_rect_objs.append(ro:=RectObj(self.portalframe_tile.rect.center, None, self.portalframe_tile.rect.size, None, WORLD_ATLAS, self.assets.get_uvs(PORTALFRAME_TILE)))
        self.can_be_above.append(self.portalframe_tile)
        self.portalframe_tile.rect_obj = ro
        
        hitbox = pygame.FRect(0, 0, self.portal_tile.rect.w/1.4, OBJ_SIZE/2)
        hitbox.midbottom = self.portalframe_tile.rect.midbottom
        self.collision_rects.append(hitbox)
        
    def add_oxygens(self):
        for topleft in self.map_loader.oxygen_positions:
            tile = Tile(self, (topleft[0]-OXYGEN_SIZE/4, topleft[1]-OXYGEN_SIZE/4), OXYGEN_SIZE, OXYGEN_TILE, is_plant=True)
            self.oxygen_tiles.append(tile), self.plant_tiles.append(tile), self.can_be_above.append(tile)
            self.plant_rect_objs.append(rectobj:=RectObj(tile.rect.center, None, tile.rect.size, None,
                                                         WORLD_ATLAS, self.assets.get_uvs(OXYGEN_TILE, "plants")))
            tile.rect_obj = rectobj
            self.bubble_spawners.append(BubbleSpawner(self, tile.rect.center))
        self.plant_rect_objs.sort(key=lambda x: x.pos[1])
        
    def build_asteroid(self):
        for tx in range(self.map_loader.min_x-MAP_PADDING, self.map_loader.max_x+MAP_PADDING):
            for ty in range(self.map_loader.min_y-MAP_PADDING, self.map_loader.max_y+MAP_PADDING):
                topleft = (tx, ty)
                if not self.map_loader.has_tile(topleft):
                    if random.randint(0, 100) <= LILSTAR_CHANCE:
                        self.add_lilstar(topleft)
                    elif random.randint(0, DUST_CHANCE_RANGE) <= 1:
                        self.add_dust(topleft)
                    elif random.randint(0, STAR_CHANCE_RANGE) <= 1:
                        self.add_star(topleft)
                else:
                    tex_name, is_height, block_id = self.map_loader.tile_data(topleft)
                    self.add_floor(topleft, tex_name) if not is_height else self.add_height(topleft, tex_name)
                    self.add_depth(topleft, tex_name)
                            
                    if block_id == LOAD_GRASS and not is_height:
                        for noise in [self.cactus_noise, self.flowers_noise, self.spiral_noise, self.grass_plant_noise]:
                            if noise.noise(topleft) < noise.activation:
                                self.add_plant(noise.tile, topleft)
                                break
                    if block_id == LOAD_ROCK and topleft[1] > self.map_loader.min_y+10:
                        for noise in [self.rove_noise, self.spores_noise]:
                            if noise.noise(topleft) < noise.activation:
                                self.add_plant(noise.tile, topleft)
                                break
                            
    def add_depth(self, topleft, tex_name):
        up = (topleft[0], topleft[1]-1)
        if tex_name in ROCKY_TILES:
            if self.map_loader.has_tile(up) and self.map_loader.tile_data(up)[-1] not in LOAD_ROCKY:
                self.add_height(topleft, HALF_GRASS_TILE, False)
                self.jump_down_rects.append(pygame.FRect(topleft, (OBJ_SIZE, HALF_COLLIDER_H)))
        if tex_name == GRASS_TILE:
            if not self.map_loader.has_tile(up) or self.map_loader.tile_data(up)[-1] != LOAD_GRASS:
                self.add_colored(topleft, FLIP_GRASS_TILE, (0.6, 0.6, 0.6, 1))
                self.jump_up_rects.append(pygame.FRect(topleft, (OBJ_SIZE, HALF_COLLIDER_H)))
        
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
                self.add_static_light(Light(plant.rect.center, *CHUNK_LIGHT_DATA[plant.tile_name]))
                lights_covered[plant.tile_name].append(plant.rect.center)
                
    def refresh_tree_lights(self):
        for light in self.tree_lights:
            self.static_light_batch.remove_light(light)
        self.tree_lights = []
        lights_covered = {tree.name: [] for tree in TreeData.get_all() if tree.has_light}
        for tree in self.trees:
            if not tree.tree.has_light:
                continue
            lights = lights_covered[tree.tree.name]
            is_far = False
            for light_pos in lights:
                if pygame.Vector2(tree.rect.center).distance_to(light_pos) < TREE_CHUNK_DIST:
                    is_far = True
                    break
            if not is_far:
                self.tree_lights.append(Light(tree.rect.center, *tree.tree.light_data))
                lights_covered[tree.tree.name].append(tree.rect.center)
        for light in self.tree_lights:
            self.static_light_batch.add_light(light)
        
    def add_dust(self, topleft):
        size = random.uniform(16/0.8, 16/0.3)
        if random.randint(0, 100) < 50:
            color = DUST1_START.lerp(DUST1_END, random.uniform(0.0, 1.0))
        else:
            color = DUST2_START.lerp(DUST2_END, random.uniform(0.0, 1.0))
        color.a = random.randint(50,100)
        self.dust_rect_objs.append(RectObj(topleft, None, (size, size), (color.r/255, color.g/255, color.b/255, color.a/255),
                                            WORLD_ATLAS, self.assets.get_uvs("particle")))
        
    def add_star(self, topleft):
        size = random.uniform(3.1, 6.1)
        name = random.choice(list(STAR_COLORS.keys()))
        self.dust_rect_objs.append(RectObj(topleft, None, (size*2.2, size*2.2), STAR_COLORS[name], WORLD_ATLAS, self.assets.get_uvs("particle")))
        self.dust_rect_objs.append(RectObj(topleft, None, (size, size), None, WORLD_ATLAS, self.assets.get_uvs(name, "stars")))
        
    def add_lilstar(self, topleft):
        pos = (topleft[0]+random.uniform(0.0, OBJ_SIZE-0.3), topleft[1] + random.uniform(0.0, OBJ_SIZE-0.3))
        color = (random.randint(200,255)/255, random.randint(200, 255)/255, random.randint(200, 255)/255, 0.8)
        size = random.uniform(OBJ_SIZE/18, OBJ_SIZE/12)
        self.dust_rect_objs.append(RectObj(pos, None, (size*3, size*3), color, WORLD_ATLAS, self.assets.get_uvs("particle")))
        self.dust_rect_objs.append(RectObj(pos, None, (size, size), color, WORLD_ATLAS, self.assets.get_uvs("square")))
        
    def add_floor(self, topleft, tex_name):
        self.tile_rect_objs.append(RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), (1, 1, 1, 1), 
                            WORLD_ATLAS, self.assets.get_uvs(tex_name)))
        self.floor_tiles[f"{int(topleft[0])};{int(topleft[1])}"] = (Tile(self, topleft, OBJ_SIZE, tex_name, True, False, False,))
        
    def add_colored(self, topleft, tex_name, color):
        self.tile_rect_objs.append(RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), color, 
                            WORLD_ATLAS, self.assets.get_uvs(tex_name)))
        
    def add_height(self, topleft, tex_name, add_tile = True):
        self.tile_rect_objs.append(RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), (0.5, 0.5, 0.5, 1), 
                            WORLD_ATLAS, self.assets.get_uvs(tex_name)))
        if add_tile:
            self.height_tiles[f"{int(topleft[0])};{int(topleft[1])}"] = Tile(self, topleft, OBJ_SIZE, tex_name, False, False, False)
    
    def add_plant(self, plant_tile, topleft):
        topleft = (topleft[0] + random.uniform(-PLANT_OFFSET, PLANT_OFFSET), topleft[1] + random.uniform(-PLANT_OFFSET, PLANT_OFFSET))
        self.plant_rect_objs.append((rect_obj:=RectObj(None, topleft, (OBJ_SIZE, OBJ_SIZE), (1, 1, 1, 1),
                                            WORLD_ATLAS, self.assets.get_uvs(plant_tile, "plants"))))
        self.plant_tiles.append(tile:=Tile(self, topleft, OBJ_SIZE, plant_tile, is_plant=True, rect_obj=rect_obj))
        if plant_tile not in [ROVE_TILE, SPORES_TILE]:
            self.can_be_above.append(tile)
            
    def add_static_light(self, light):
        self.static_light_batch.add_light(light)
        
    def add_dynamic_light(self, light):
        self.dynamic_light_batch.add_light(light)
    
    def remove_static_light(self, light):
        self.static_light_batch.remove_light(light)
        
    def remove_dynamic_light(self, light):
        self.dynamic_light_batch.remove_light(light)
        
    def free_buffers(self):
        self.dust_rects_batch.free_rect_objs()
        self.dust_rect_objs = []
        self.tile_rect_objs = []
        self.plant_rect_objs = []
    
    def update(self):
        self.health += camera.dt*CURE_AMOUNT
        if self.health > self.map.health:
            self.health = self.map.health
            
        self.portal_angle += PORTAL_ROT_SPEED*camera.dt
        #self.portal_tile.rect_obj.update_positions(self.portal_tile.rect.center, None, self.portal_tile.rect.size, self.portal_angle)
            
        self.player.update()
        self.spawner.update()
        
        for tree in self.trees:
            tree.update()
        for enemy in self.enemies:
            enemy.update()
        for building in self.buildings:
            building.update()
        for bot in self.bots:
            bot.update()
        for particle in self.uparticles:
            particle.update()
        for bs in self.bubble_spawners:
            bs.update()
            
        if len(self.enemies)+len(self.bots) > 0:
            self.update_bots_batch()
        if len(self.uparticles) >= 0:
            self.uparticles_batch.update_rects()
        
        self.random_unlit_batch.update_rects()
        self.above_batch.update_rects(self.get_above_player(self.can_be_above))
        self.above_unlit_batch.update_rects(self.get_above_player(self.can_be_above_unlit))
        self.dynamic_light_batch.update_buffer()
        
        pygame.display.set_caption(f"{TITLE} - {camera.clock.get_fps():.0f}")
        
    def light_filter(self, light: Light):
        return light.rect.colliderect(camera.rect)
        
    def render(self):
        camera.upload_uniforms(LIT_SHADER, UNLIT_SHADER, REPLACE_SHADER)
        TextureBatch.upload_samplers(MAX_SAMPLERS, "textures", LIT_SHADER, UNLIT_SHADER, REPLACE_SHADER)
        self.dynamic_light_batch.filter(), self.static_light_batch.filter()
        LightBatch.upload_uniform(self.static_light_batch, self.dynamic_light_batch, LIT_SHADER, MAX_LIGHTS)
        self.assets.use()
        
        self.dust_rects_batch.render()
        self.tile_rects_batch.render()
        self.buildings_batch.render()
        self.random_unlit_batch.render()
        self.bots_batch.render()
        self.player.render()
        self.uparticles_batch.render()
        self.above_batch.render()
        self.above_unlit_batch.render()
        
    def get_above_player(self, list_from):
        above_rect_objs = []
        for tile in list_from:
            if len(above_rect_objs) >= MAX_CAN_BE_ABOVE:
                break
            if self.player.pos.distance_to(tile.rect.center) < ABOVE_MAX_DIST:
                if tile.rect.colliderect(self.player.rect) and tile.rect.bottom > self.player.hitbox.bottom:
                    above_rect_objs.append(tile.rect_obj)
        return above_rect_objs
    
    def event(self, event: pygame.Event):
        self.player.event(event)
    
    def can_build(self, building, pos, only_ore=False, only_grassy=False, only_oxygen=False, is_bot = False, need_energy=False):
        tile_pos = pos
        if building.size > 1:
            tile_pos = (pos[0], pos[1]+1)
        floor_tile = self.get_floor_tile(tile_pos)
        if floor_tile is None or floor_tile.tile_name == ROCK_TILE:
            return False
        if only_ore:
            if floor_tile.tile_name not in ROCKY_TILES:
                return False
        if only_grassy or only_oxygen:
            if floor_tile.tile_name in ROCKY_TILES:
                return False
        if only_oxygen:
            one_collided = False
            for otile in self.oxygen_tiles:
                if otile.rect.colliderect(floor_tile.rect):
                    one_collided = True
                    break
            if not one_collided:
                return False
        if not is_bot:
            rect = pygame.FRect(pos[0]-building.size/2/2, pos[1]-building.size/2/2, building.size/2, building.size/2)
            for b in self.buildings:
                if b.rect.contains(rect) or rect.contains(b.rect):
                    return False
            for tree in self.trees:
                if tree.rect.contains(rect) or rect.contains(tree.rect):
                    return False
        if need_energy:
            one_found = False
            for b in self.energy_buildings:
                if pygame.Vector2(b.rect.center).distance_to(pos) <= ENERGY_DISTANCE:
                    one_found = True
                    break
            if not one_found:
                return False
        return True        
        
    def get_floor_tile(self, pos):
        pos = f"{int(pos[0]) if pos[0] > 0 else int(pos[0]-1)};{int(pos[1]) if pos[1] > 0 else int(pos[1]-1)}"
        if pos in self.floor_tiles:
            return self.floor_tiles[pos]
        
    def get_tile(self, pos):
        pos = f"{int(pos[0]) if pos[0] > 0 else int(pos[0]-1)};{int(pos[1]) if pos[1] > 0 else int(pos[1]-1)}"
        if pos in self.height_tiles:
            return self.height_tiles[pos]
        if pos in self.floor_tiles:
            return self.floor_tiles[pos]
        