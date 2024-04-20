from .engine.prelude import *
import random
import typing
if typing.TYPE_CHECKING:
    from .tree import Tree
    from .world import World
    
from .enemy import Enemy
from .particle import Proj, GrowingParticle, GrowingParticleY, Particle
from . import god

from .consts import *

class TreeAttack:
    def __init__(self, tree: "Tree"):
        self.tree: "Tree" = tree
        self.tree_data = tree.tree
        self.last_attack = -10000
        self.enemy: Enemy = None
        self.can_attack = True
        
    def base_update(self):
        if not self.can_attack:
            return False
        if self.tree.energy < self.tree.tree.energy_price:
            return False
        if camera.get_ticks() - self.last_attack > self.tree_data.attack_cooldown*1000:
            enemy = self.choose_enemy(self.available_enemies())
            if enemy:
                self.enemy = enemy
                self.last_attack = camera.get_ticks()
                self.start_attack()
                god.sounds.play_random("attack")
                
    def update(self):
        self.base_update()
                
    def available_enemies(self, invis_enemies=[], start=None):
        if start is None:
            start = self.tree.pos
        enemies = []
        for enemy in (god.world.enemies):
            if enemy not in invis_enemies and pygame.Vector2(start).distance_to(enemy.rect.center) <= self.tree_data.attack_range:
                enemies.append(enemy)
        return enemies
    
    def choose_enemy(self, enemies: list[Enemy]):
        if len(enemies) <= 0:
            return None
        if len(enemies) == 1:
            return enemies[0]
        else:
            sorted_enemies = sorted(enemies, key=(lambda e: e.enemy.speed*e.enemy.health))
            #for e in sorted_enemies:
            #    if e not in self.world.enemies_shot:
            #        return e
            return sorted_enemies[0]
                
    def predict_enemy_pos(self, enemy=None):
        if enemy is None:
            enemy = self.enemy
        return enemy.rect.center+(enemy.direction*(((enemy.enemy.speed*enemy.speed_mul*enemy.buff.speed_mul)/self.tree_data.proj["speed"])
                                                   *self.tree.pos.distance_to(enemy.rect.center)))
    
    def get_size_offset(self):
        inflate, offset = self.tree_data.proj.get("inflate", 0.09), self.tree_data.proj.get("offset", 0.11)
        return (random.uniform(-inflate, inflate), 
                (random.uniform(-offset, offset), random.uniform(-offset, offset)))
    
    def start_attack(self):
        ...
        
    def shoot(self, pos, size, dir, proj, attrs=None, invis_enemies=None, target=None):
        god.world.add_uparticle(Proj(pos, size, dir, self.tree, proj, attrs, invis_enemies))
        if target and target not in god.world.enemies_shot:
            god.world.enemies_shot.append(target)
        
    def hit_effect(self, enemy: Enemy):
        if self.tree_data.has_effect:
            extra = list(filter((lambda x: x[0] not in ["name", "ticks"]), list(self.tree_data.effect.items())))[0][1]
            enemy.add_effect(self.tree_data.effect["name"], self.tree_data.effect["ticks"], extra)
        if enemy in god.world.enemies_shot:
            god.world.enemies_shot.remove(enemy)
        
    def hit(self, enemy: Enemy, proj):
        self.hit_effect(enemy)
                
    def get_dir(self, predicted, start=None):
        if start is None:
            start = self.tree.pos
        return -(pygame.Vector2(start)-predicted).normalize()
        
class AttackSingle(TreeAttack):
    def __init__(self, tree):
        super().__init__(tree)
        self.proj = self.tree.tree.proj
        
    def start_attack(self):
        esize, eoffset = self.get_size_offset()
        self.tree.consume_energy()
        self.shoot(self.tree.pos+eoffset, (self.proj["size"][0]+esize, self.proj["size"][1]+esize), self.get_dir(self.predict_enemy_pos()), self.proj, target=self.enemy)
        
class AttackHitSplit(AttackSingle):
    def __init__(self, tree):
        super().__init__(tree)
            
    def hit(self, enemy: Enemy, proj: Proj):
        self.hit_effect(enemy)
        if "is_split" in proj.attrs:
            return
        for dir in [pygame.Vector2(1, 0), pygame.Vector2(-1, 0), pygame.Vector2(0, 1), pygame.Vector2(0, -1),
                    pygame.Vector2(1, 1).normalize(), pygame.Vector2(-1, -1).normalize(), 
                    pygame.Vector2(1, -1).normalize(), pygame.Vector2(-1, 1).normalize()]:
            self.shoot(proj.rect.center, self.tree_data.split["size"], dir, self.tree_data.split, {"is_split": True}, [enemy])
            
class AttackHitArea(AttackSingle):
    def __init__(self, tree):
        super().__init__(tree)
        self.area = self.tree_data.area
        
    def hit(self, enemy: Enemy, proj: Proj):
        self.hit_effect(enemy)
        class_name = GrowingParticleY if self.area.get("y", False) else GrowingParticle
        god.world.add_uparticle(class_name(proj.rect.center, [0, 0], self.area["radius"]*2, self.area["grow_time"], 
                                                 self.area.get("disappear_time", 0.2), self.area["tex_name"], self.area.get("frames", 0), self.area.get("color", WHITE), self.area.get("frame_speed", 0)))
        for enemy in god.world.enemies:
            if pygame.Vector2(enemy.rect.center).distance_to(proj.rect.center) <= self.area["radius"]:
                enemy.damage(self.area["damage"])
                
class AttackHitSequence(AttackSingle):
    def __init__(self, tree):
        super().__init__(tree)
        self.sequence = self.tree_data.sequence
        
    def hit(self, enemy: Enemy, proj: Proj):
        self.hit_effect(enemy)
        if len(proj.invis_enemies) >= self.sequence["amount"]-1:
            return
        new_enemy: Enemy = self.choose_enemy(self.available_enemies(proj.invis_enemies, proj.rect.center))
        if new_enemy is not None:
            self.shoot(proj.rect.center, self.proj["size"], self.get_dir(self.predict_enemy_pos(new_enemy), proj.rect.center), self.proj, None, proj.invis_enemies+[enemy], new_enemy)
    
class AttackBurst(TreeAttack):
    def __init__(self, tree):
        super().__init__(tree)
        self.proj = self.tree_data.proj
        self.burst = self.tree_data.burst
        self.attacking = False
        self.spawn_amount = 0
        self.last_spawn = camera.get_ticks()
        
    def start_attack(self):
        self.attacking = True
        self.spawn_amount = 0
        self.attack()
        
    def attack(self):
        self.spawn_amount += 1
        if self.spawn_amount >= self.burst["amount"]:
            self.attacking = False
        self.last_spawn = camera.get_ticks()
        esize, eoffset = self.get_size_offset()
        self.tree.consume_energy()
        self.shoot(self.tree.pos+eoffset, (self.proj["size"][0]+esize, self.proj["size"][1]+esize), self.get_dir(self.predict_enemy_pos()), self.proj, target=self.enemy)
        
    def update(self):
        self.base_update()
        if self.attacking:
            if camera.get_ticks() - self.last_spawn >= self.burst["cooldown"]*1000:
                self.attack()
                
class AttackSpawn(TreeAttack):
    def __init__(self, tree):
        super().__init__(tree)
        
    def start_attack(self):
        self.tree.consume_energy()
        god.world.add_uparticle(GrowingParticleY(self.enemy.rect.center, (self.tree_data.area["radius"], 0), self.tree_data.area["radius"], 
                                                  self.tree_data.area["grow_time"], self.tree_data.area.get("disappear_time", 0.2), self.tree_data.area["tex_name"],
                                                  self.tree_data.area.get("frames", 0), self.tree_data.area.get("color", WHITE), self.tree_data.area.get("frame_speed", 0)))
        for enemy in god.world.enemies:
            if pygame.Vector2(enemy.rect.center).distance_to(self.enemy.rect.center) <= self.tree_data.area["radius"]:
                enemy.damage(self.tree_data.area["damage"])

class AttackBeam(TreeAttack):
    def __init__(self, tree):
        super().__init__(tree)
        self.beam = self.tree_data.beam
        self.last_tick = 0
        self.ticks = 0
        
    def start_attack(self):
        self.can_attack = False
        self.last_tick = camera.get_ticks()
        self.ticks = 0
        self.particle = Particle((0, 0), (self.beam["size"], 1), self.beam.get("tex_name", "square"), 0, self.beam.get("color", WHITE), 0)
        god.world.add_uparticle(self.particle)
        self.update_particle()
    
    def update(self):
        self.base_update()
        if self.tree.energy < self.tree.tree.energy_price:
            return
        if not self.can_attack:
            self.update_particle()
            
            if self.enemy.health <= 0:
                self.can_attack = True
                self.particle.destroy()
                return
            
            if camera.get_ticks() - self.last_tick >= TICK*1000:
                self.last_tick = camera.get_ticks()
                self.ticks += 1
                if self.ticks >= self.beam["ticks"]:
                    self.can_attack = True
                    self.particle.destroy()
                    
                if self.enemy.health > 0:
                    self.enemy.damage(self.beam["damage"])
                    self.tree.consume_energy()
                    
    def update_particle(self):
        direction = self.enemy.rect.center-self.tree.pos
        particle_height, particle_angle, particle_center = direction.magnitude(), direction.as_polar()[1]+90, (direction.x/2, direction.y/2)
        
        self.particle.rect.center = particle_center+self.tree.pos
        self.particle.rect.size = (self.particle.rect.w, particle_height)
        self.particle.angle = particle_angle
        self.particle.update_rect_obj()
            
        
ATTACK_CLASSES = {
    "single": AttackSingle,
    "burst": AttackBurst,
    "split": AttackHitSplit,
    "area": AttackHitArea,
    "sequence": AttackHitSequence,
    "spawn": AttackSpawn,
    "beam": AttackBeam
}
