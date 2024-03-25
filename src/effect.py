from .engine.prelude import *
import random

from .consts import *
from .particle import MovingParticle, GrowingParticle, Particle

class AttackEffect:
    def __init__(self, enemy, name, ticks):
        self.enemy, self.name, self.ticks = enemy, name, ticks
        self.last_tick = pygame.time.get_ticks()
        self.ticks_passed = 0
        
    def update(self):
        if pygame.time.get_ticks() - self.last_tick > TICK*1000:
            self.ticks_passed += 1
            self.last_tick = pygame.time.get_ticks()
            self.tick()
            if self.ticks_passed >= self.ticks:
                self.destroy()
        self.extra_update()
                
    def extra_update(self):
        ...
        
    def tick(self):
        ...
        
    def on_destroy(self):
        ...
        
    def destroy(self):
        self.on_destroy()
        del self.enemy.effects[self.name]
        
class FireEffect(AttackEffect):
    def __init__(self, enemy, name, ticks, damage):
        super().__init__(enemy, name, ticks)
        self.damage = damage
        
    def tick(self):
        self.enemy.damage(self.damage, True)
        
class PoisonEffect(AttackEffect):
    def __init__(self, enemy, name, ticks, damage):
        super().__init__(enemy, name, ticks)
        self.damage = damage
        
    def tick(self):
        size = EFFECT_PARTICLE_SIZE + random.uniform(-0.11, 0.11)
        self.enemy.world.add_uparticle(MovingParticle(self.enemy.world, self.enemy.rect.center, (size, size), (0, -1), EFFECT_PARTICLE_DIST, EFFECT_PARTICLE_SPEED,
                                                            "skull", 0, (0, 0.7, 0, 1)))
        self.enemy.damage(self.damage, True)
                
class GellyEffect(AttackEffect):
    def __init__(self, enemy, name, ticks, speed_mul):
        super().__init__(enemy, name, ticks)
        self.enemy.speed_mul = speed_mul
        self.particle = Particle(self.enemy.world, self.enemy.rect.center, (1.2, 1.2), "gellyeffect", 0, (1, 0, 1, 0.5))
        self.enemy.world.add_uparticle(self.particle)
        
    def extra_update(self):
        self.particle.rect.center = self.enemy.rect.center
        self.particle.update_rect_obj()
    
    def on_destroy(self):
        self.particle.destroy()
        self.enemy.speed_mul = 1
        
class EnemyBuff:
    def __init__(self, enemy):
        self.enemy = enemy
        self.speed_mul = 1
        
    def can_damage(self, is_effect):
        return True
    
    def can_effect(self):
        return True
    
    def update(self):
        ...
        
    def spawn_effect(self, name, col):
        size = EFFECT_PARTICLE_SIZE + random.uniform(-0.11, 0.11)
        self.enemy.world.add_uparticle(MovingParticle(self.enemy.world, self.enemy.rect.center, (size, size), (0, -1), EFFECT_PARTICLE_DIST, EFFECT_PARTICLE_SPEED,
                                                            name, 0, col))
                
class CureBuff(EnemyBuff):
    def __init__(self, enemy):
        super().__init__(enemy)
        self.last_heal = 0
        
    def can_damage(self, is_effect):
        self.last_heal = pygame.time.get_ticks()
        return True
        
    def update(self):
        if self.enemy.health < self.enemy.enemy.health:
            if pygame.time.get_ticks() - self.last_heal > BUFF_HEAL_COOLDOWN*1000:
                self.last_heal = pygame.time.get_ticks()
                self.enemy.heal(BUFF_HEAL_AMOUNT)
                self.spawn_effect("plus", (0, 1, 0, 1))
            
class OnlyEffectBuff(EnemyBuff):
    def __init__(self, enemy):
        super().__init__(enemy)
        
    def can_damage(self, is_effect):
        if is_effect:
            return True
        self.spawn_effect("stop", (1, 0, 0, 1))
        return False
        
class ArmorBuff(EnemyBuff):
    def __init__(self, enemy):
        super().__init__(enemy)
        self.hits = 0
        
    def can_damage(self, is_effect):
        if self.hits > BUFF_ARMOR_HITS:
            return True
        self.hits += 1
        self.spawn_effect("armor", (0, 0, 0.9, 1))
        return False
        
class RageBuff(EnemyBuff):
    def __init__(self, enemy):
        super().__init__(enemy)
        
    def update(self):
        x = 1-(self.enemy.health/self.enemy.enemy.health)
        self.speed_mul = 1+((BUFF_MAX_SPEED-1)*x)
        
class SpeedBuff(EnemyBuff):
    def __init__(self, enemy):
        super().__init__(enemy)
        self.speed_mul = BUFF_MAX_SPEED
        
    def update(self):
        x = self.enemy.follow_pos_idx/len(self.enemy.world.follow_pos)
        self.speed_mul = BUFF_MAX_SPEED-(x*(BUFF_MAX_SPEED-1))
        
class NoEffectBuff(EnemyBuff):
    def __init__(self, enemy):
        super().__init__(enemy)
        
    def can_effect(self):
        self.spawn_effect("stop", (1, 0, 0, 1))
        return False
        
    def can_damage(self, is_effect):
        return not is_effect
        
class TeleportBuff(EnemyBuff):
    def __init__(self, enemy):
        super().__init__(enemy)
        half_idx = len(self.enemy.world.follow_pos)//2
        self.enemy.rect.center = self.enemy.world.follow_pos[half_idx]
        self.enemy.follow_pos_idx = half_idx+1
        self.enemy.next_follow_pos = self.enemy.world.follow_pos[half_idx+1]
        self.enemy.next_rect = self.enemy.world.follow_rects[half_idx+1]
        self.enemy.update_pos()
        self.enemy.world.add_uparticle(GrowingParticle(self.enemy.world, self.enemy.rect.center, (1.5, 1.5), 2.5, 0.05, 0.5, "enemyportal"))
        
ATTACK_EFFECTS = {
    "fire": FireEffect,
    "poison": PoisonEffect,
    "gelly": GellyEffect,
}

ENEMY_BUFFS = {
    "cure": CureBuff,
    "only_effect": OnlyEffectBuff,
    "no_effect": NoEffectBuff,
    "armor": ArmorBuff,
    "rage": RageBuff,
    "cure": CureBuff,
    "speed": SpeedBuff,
    "teleport": TeleportBuff
}
