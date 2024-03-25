from .engine.prelude import *

from .consts import *
from .effect import ATTACK_EFFECTS, AttackEffect, EnemyBuff, ENEMY_BUFFS

class Enemy:
    def __init__(self, world, enemy: EnemyData, pos):
        self.world, self.enemy = world, enemy
        self.rect = pygame.FRect(0, 0, self.enemy.size, self.enemy.size)
        self.rect.center = pos
        if self.enemy.has_light:
            self.light = Light(list(pos), *self.enemy.light_data)
            self.world.add_dynamic_light(self.light)
        self.right_uvs = self.world.assets.get_uvs(self.enemy.tex_name)
        self.left_uvs = self.world.assets.get_uvs(self.enemy.tex_name, flipx=True)
        self.rect_obj = RectObj(pos, None, (self.enemy.size, self.enemy.size), None,
                                WORLD_ATLAS, self.right_uvs)
        self.follow_pos_idx = 0
        self.next_follow_pos = self.world.follow_pos[0]
        self.next_rect = self.world.follow_rects[0]
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
            self.world.boss_spawned()
        
    def add_effect(self, name, ticks, *args):
        if not self.buff.can_effect():
            return
        if name not in self.effects:
            self.effects[name] = ATTACK_EFFECTS[name](self, name, ticks, *args)
        
    def damage(self, damage, is_effect=False):
        if damage > 0 and self.buff.can_damage(is_effect):
            self.health -= damage
            self.last_damage = pygame.time.get_ticks()
            if self in self.world.enemies_shot:
                self.world.enemies_shot.remove(self)
            if self.health <= 0:
                self.health = 0
                self.world.player.add_money(self.enemy.reward)
                self.destroy()
                
    def heal(self, amount):
        self.health += amount
        if self.health > self.enemy.health:
            self.health = self.enemy.health

    def update_pos(self):
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
                if self.follow_pos_idx >= len(self.world.follow_pos):
                    self.follow_pos_idx = -1
                    self.next_rect = None
                    self.world.damage(self.health)
                    self.destroy()
                else:
                    self.next_rect = self.world.follow_rects[self.follow_pos_idx]
                    self.next_follow_pos = self.world.follow_pos[self.follow_pos_idx]
        if pygame.time.get_ticks() - self.last_damage > ENEMY_DAMAGE_COOLDOWN*1000:
            self.rect_obj.color = WHITE
        else:
            self.rect_obj.color = ENEMY_DAMAGE_COL
            
                    
    def destroy(self):
        if self in self.world.enemies_shot:
            self.world.enemies_shot.remove(self)
        if self.enemy.has_light:
            self.world.remove_dynamic_light(self.light)
        for effect in list(self.effects.values()):
            effect.on_destroy()
        self.world.spawner.enemy_destroyed()
        self.world.remove_enemy(self)
