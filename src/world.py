from .engine.prelude import *

from .consts import *
from .player import Player
from .world_props import MapLoader, EnemyWaveSpawner, WorldBuilder
from .tree import Tree
from .enemy import Enemy
from .building import Building, BotBuilding, MinerBuilding
from .world_ui import WorldUI
from . import god

class World(Scene):
    def init(self, map: MapData):
        god.world = self
        god.sounds.play("alien")
        god.sounds.music_play("world_music")
        camera.zoom = 0.5
        camera.make_proj()
        
        self.map = map
        self.health = self.map.health
        self.map_loader = MapLoader(self.map)
        self.spawner = EnemyWaveSpawner()
        self.builder = WorldBuilder()
        
        self.silly_obj = [RectObj((1, 1), None, (0.001, 0.001), None, 2, None)]
        self.floor_tiles, self.height_tiles = {}, {}
        self.plant_tiles, self.oxygen_tiles = [], []
        self.can_be_above, self.can_be_above_unlit = [], []
        
        self.jump_up_rects, self.jump_down_rects, self.depth_rects = [], [], []
        self.collision_rects = self.map_loader.collisions
        self.bubble_spawners = []
        
        self.static_light_batch, self.dynamic_light_batch = LightBatch(self.light_filter), LightBatch(self.light_filter)
        self.player = Player()
        self.ui = WorldUI()
        self.ui.pause.settings.build()
        
        self.trees: list[Tree] = []
        self.buildings: list[Building] = []
        self.energy_buildings: list[Building] = []
        self.miner_buildings: list[MinerBuilding] = []
        self.all_building_like: list[Tree|Building] = []
        self.tree_lights: list[Light] = []
        self.miner_lights: list[Light] = []
        self.buildings_batch_top = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        self.buildings_batch_bottom = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        
        self.enemies: list[Enemy] = []
        self.bots: list[BotBuilding] = []
        self.bots_rect_objs = []
        self.bots_batch = GrowingRectsBatch(LIT_SHADER, *SHADER_UNIFORMS)
        
        self.uparticles = []
        self.uparticles_rect_objs = []+self.silly_obj
        self.uparticles_batch = GrowingRectsBatch(UNLIT_SHADER, *SHADER_UNIFORMS)
        
        self.follow_pos = [pygame.Vector2(sp) for sp in self.map_loader.sorted_pos]
        self.follow_rects = [pygame.FRect(sp.x, sp.y, 0.2, 0.2) for sp in self.follow_pos]
        
        self.builder.build()
        
        self.above_batch = FixedRectsBatch([], True, MAX_CAN_BE_ABOVE).create_vao(LIT_SHADER, *SHADER_UNIFORMS)
        self.above_unlit_batch = FixedRectsBatch([], True, MAX_CAN_BE_ABOVE).create_vao(UNLIT_SHADER, *SHADER_UNIFORMS)
        self.random_unlit_batch = FixedRectsBatch([self.builder.portal_tile.rect_obj], True).create_vao(UNLIT_SHADER, *SHADER_UNIFORMS)
                
        self.builder.free_buffers()
        
        self.portal_angle = 0
        self.last_damage = -9999
        self.forced_refresh = camera.get_ticks()

    def boss_spawned(self):
        self.random_unlit_batch.rect_objs.remove(self.builder.portal_tile.rect_obj)
        self.random_unlit_batch.update_rects()
        self.builder.tile_rects_batch.rect_objs.remove(self.builder.portalframe_tile.rect_obj)
        self.builder.tile_rects_batch.update_rects()
        self.builder.tile_rects_batch.free_rect_objs()
        self.remove_static_light(self.builder.spawner_light)
        self.can_be_above_unlit.remove(self.builder.portal_tile)
        self.can_be_above.remove(self.builder.portalframe_tile)
        self.collision_rects.remove(self.builder.portal_hitbox)
        
    def damage(self, damage):
        self.health -= damage
        self.last_damage = camera.get_ticks()
        god.sounds.play("explosion")
        if self.health <= 0:
            print("Game over lmao")
            self.manager.quit()
        self.ui.update_static()
            
    def add_uparticle(self, particle):
        self.uparticles.append(particle)
        self.uparticles_rect_objs.append(particle.rect_obj)
        
    def remove_uparticle(self, particle):
        self.uparticles.remove(particle)
        self.uparticles_rect_objs.remove(particle.rect_obj)
        
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
        self.all_building_like.append(building)
        self.refresh_building_like()
        
    def remove_building_like(self, building):
        self.all_building_like.remove(building)
        self.refresh_building_like()
        
    def refresh_building_like(self):
        self.sort()
        self.update_split()
    
    def update_bots_batch(self):
        self.bots_batch.update_rects(self.bots_rect_objs)
        
    def sort(self):
        self.all_building_like.sort(key=lambda obj: obj.rect.centery)
        self.enemies.sort(key=lambda enemy: enemy.rect.center)
        self.can_be_above.sort(key=lambda obj: obj.rect.centery)
        
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
            
    def refresh_miner_lights(self):
        for light in self.miner_lights:
            self.static_light_batch.remove_light(light)
        self.miner_lights = []
        lights = []
        for miner in self.miner_buildings:
            if not miner.can_work:
                continue
            is_far = False
            for light_pos in lights:
                if miner.pos.distance_to(light_pos) < MINER_CHUNK_DIST:
                    is_far = True
                    break
            if not is_far:
                self.miner_lights.append(Light(miner.rect.center, *miner.building.light_data))
                lights.append(miner.rect.center)
        for light in self.miner_lights:
            self.static_light_batch.add_light(light)
            
    def add_static_light(self, light):
        self.static_light_batch.add_light(light)
        
    def add_dynamic_light(self, light):
        self.dynamic_light_batch.add_light(light)
    
    def remove_static_light(self, light):
        self.static_light_batch.remove_light(light)
        
    def remove_dynamic_light(self, light):
        self.dynamic_light_batch.remove_light(light)
    
    def update(self):
        god.menu = None
        if not self.spawner.wave_active:
            self.health += camera.dt*CURE_AMOUNT
        if self.health > self.map.health:
            self.health = self.map.health
            
        self.portal_angle += PORTAL_ROT_SPEED*camera.dt
        #self.portal_tile.rect_obj.update_positions(self.portal_tile.rect.center, None, self.portal_tile.rect.size, self.portal_angle)
            
        self.player.update()
        self.spawner.update()
        self.ui.update()
            
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
            
        if camera.get_ticks() - self.forced_refresh > 1000:
            self.forced_refresh = camera.get_ticks()
            
        if len(self.enemies)+len(self.bots) > 0:
            self.update_bots_batch()
        self.uparticles_batch.update_rects(self.uparticles_rect_objs)
        
        if self.player.dir.length() != 0:
            self.update_split()
        
        self.random_unlit_batch.update_rects()
        self.above_batch.update_rects(self.get_above_player(self.can_be_above))
        self.above_unlit_batch.update_rects(self.get_above_player(self.can_be_above_unlit))
        self.dynamic_light_batch.update_buffer()

        self.dynamic_light_batch.filter(), self.static_light_batch.filter()
        
    def update_split(self):
        below_b, above_b = self.split_above_player(self.all_building_like)
        self.buildings_batch_bottom.update_rects(below_b+self.silly_obj)
        self.buildings_batch_top.update_rects(above_b+self.silly_obj)
        
    def light_filter(self, light: Light):
        return light.rect.colliderect(camera.world_rect)
        
    def render(self):
        LightBatch.upload_uniform(self.static_light_batch, self.dynamic_light_batch, 
                                  LIT_SHADER, god.settings.max_lights)
        
        self.builder.render()
        #self.buildings_batch.render()
        self.buildings_batch_bottom.render()
        self.random_unlit_batch.render()
        self.bots_batch.render()
        self.player.render()
        self.buildings_batch_top.render()
        self.uparticles_batch.render()
        self.above_batch.render()
        self.above_unlit_batch.render()
        self.player.post_render()

        self.ui.render()
        
    def get_above_player(self, list_from):
        above_rect_objs = []
        for tile in list_from:
            if len(above_rect_objs) >= MAX_CAN_BE_ABOVE:
                break
            if self.player.pos.distance_to(tile.rect.center) < ABOVE_MAX_DIST:
                if tile.rect.bottom > self.player.hitbox.bottom and tile.rect.colliderect(self.player.rect):
                    above_rect_objs.append(tile.rect_obj)
        return sorted(above_rect_objs, key=lambda r: r.pos[1])
    
    def split_above_player(self, list_from: list[Tree|Building]):
        below, above = [], []
        for tile in list_from:
            if tile.rect.bottom > self.player.hitbox.bottom:
                above.append(tile.rect_obj)
            else:
                below.append(tile.rect_obj)
        return below, above
    
    def event(self, event: pygame.Event):
        self.ui.event(event)
        self.ui.pause.settings.event(event)
        self.player.event(event)
        if event.type == pygame.VIDEORESIZE:
            self.ui.build()
    
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
            for rect in self.depth_rects:
                if rect.collidepoint((tile_pos[0], tile_pos[1]-OBJ_SIZE/3)):
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
                if b.pos.distance_to(pos) <= ENERGY_DISTANCE:
                    one_found = True
                    break
            if not one_found:
                return False
        return True        
    
    def refresh_buiding_energy(self):
        for b in self.energy_buildings:
            if b.building.name != ENERGY_SOURCE:
                b.has_energy = False
        for _ in range(len(self.energy_buildings)):
            for enb in self.energy_buildings:
                if enb.has_energy or enb.building.name == ENERGY_SOURCE:
                    continue
                for other in self.energy_buildings:
                    if other is not enb and other.has_energy and enb.pos.distance_to(other.pos) <= ENERGY_DISTANCE:
                        enb.has_energy = True
                        break
        for miner in self.miner_buildings:
            one_found = False
            for enb in self.energy_buildings:
                if enb.has_energy and enb.pos.distance_to(miner.pos) <= ENERGY_DISTANCE:
                    one_found = True
                    break
            if one_found:
                miner.enable_working()
            else:
                miner.disable_working()
        
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
        