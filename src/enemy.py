from .engine.prelude import *

from .consts import *
from .effect import ATTACK_EFFECTS, AttackEffect, EnemyBuff, ENEMY_BUFFS
from .ui import ProgressBar
from . import god

class Enemy:
    def __init__(self, enemy: EnemyData, pos):
        self.enemy = enemy
        self.rect = pygame.FRect(0, 0, self.enemy.size, self.enemy.size)
        self.rect.center = pos
        if self.enemy.has_light:
            self.light = Light(list(pos), *self.enemy.light_data)
            god.world.add_dynamic_light(self.light)
        self.right_uvs = god.assets.get_uvs(self.enemy.tex_name)
        self.left_uvs = god.assets.get_uvs(self.enemy.tex_name, flipx=True)
        self.rect_obj = RectObj(pos, None, (self.enemy.size, self.enemy.size), None,
                                WORLD_ATLAS, self.right_uvs)
        self.follow_pos_idx = 0
        self.next_follow_pos = god.world.follow_pos[0]
        self.next_rect = god.world.follow_rects[0]
        self.health = self.enemy.health
        self.last_damage = -1000
        self.direction = pygame.Vector2()
        self.speed_mul = 1
        self.effects: dict[str, AttackEffect] = {}
        self.angle = 0
        if self.enemy.has_buff:
            self.buff: EnemyBuff = ENEMY_BUFFS[self.enemy.buff](self)
        else:
            self.buff = EnemyBuff(self)
        if self.enemy.name == "boss_bot":
            god.world.boss_spawned()
        
    def add_effect(self, name, ticks, *args):
        if self.health <= 0:
            return
        if not self.buff.can_effect():
            return
        if name not in self.effects:
            self.effects[name] = ATTACK_EFFECTS[name](self, name, ticks, *args)
        
    def damage(self, damage, is_effect=False):
        if damage > 0 and self.buff.can_damage(is_effect):
            self.health -= damage
            self.last_damage = camera.get_ticks()
            if self in god.world.enemies_shot:
                god.world.enemies_shot.remove(self)
            if self.health <= 0:
                self.health = 0
                god.player.add_money(self.enemy.reward)
                god.player.add_xp(self.enemy.xp)
                self.destroy()
                
    def heal(self, amount):
        self.health += amount
        if self.health > self.enemy.health:
            self.health = self.enemy.health

    def update_pos(self):
        if self.rect.colliderect(camera.world_rect):
            self.rect_obj.update_positions(self.rect.center, None, (self.enemy.size, self.enemy.size), self.angle)
        if self.enemy.has_light:
            self.light.rect.center = self.rect.center
        
    def update(self):
        for effect in list(self.effects.values()):
            effect.update()
        self.buff.update()
        if self.follow_pos_idx >= 0:
            if self.enemy.name == "boss_bot":
                self.angle += PORTAL_ROT_SPEED*camera.dt
            dir = (self.next_follow_pos-self.rect.center).normalize()
            direction = dir*self.enemy.speed*self.speed_mul*self.buff.speed_mul*camera.dt
            self.rect.center += direction
            if direction.x > 0:
                self.rect_obj.uv = self.right_uvs
            elif direction.x < 0:
                self.rect_obj.uv = self.left_uvs
            self.direction = dir
            self.update_pos()
            if self.next_rect.colliderect(self.rect):
                self.follow_pos_idx += 1
                if self.follow_pos_idx >= len(god.world.follow_pos):
                    self.follow_pos_idx = -1
                    self.next_rect = None
                    god.world.damage(self.health)
                    self.destroy()
                else:
                    self.next_rect = god.world.follow_rects[self.follow_pos_idx]
                    self.next_follow_pos = god.world.follow_pos[self.follow_pos_idx]
        if camera.get_ticks() - self.last_damage > ENEMY_DAMAGE_COOLDOWN*1000:
            self.rect_obj.color = WHITE
        else:
            self.rect_obj.color = ENEMY_DAMAGE_COL
            
    def get_health_rect_objs(self):
        return ProgressBar.runtime_rect_objs((self.rect.w*WORLD_BAR_XMUL, WORLD_BAR_H), WORLD_BAR_C, self.health, self.enemy.health,
                                             (self.rect.centerx, self.rect.bottom+WORLD_BAR_H), HEALTH_BAR_FILL, HEALTH_BAR_BG, outline="m")        
                    
    def destroy(self):
        if self in god.world.enemies_shot:
            god.world.enemies_shot.remove(self)
        if self.enemy.has_light:
            god.world.remove_dynamic_light(self.light)
        for effect in list(self.effects.values()):
            effect.on_destroy()
        god.world.spawner.enemy_destroyed()
        god.world.remove_enemy(self)
