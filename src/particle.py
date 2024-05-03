from .engine.prelude import *

from .consts import *
from . import god

class Particle:
    def __init__(self, pos, size, tex_name, frames=0, col=None, frame_speed=0, duration=0):
        self.rect = pygame.FRect((0, 0), (size[0], size[1]))
        self.rect.center = pos
        self.rect_obj = RectObj(pos, None, size, col, WORLD_ATLAS,
                                god.assets.get_uvs(tex_name if frames <= 0 else f"{tex_name}0"))
        self.angle = 0
        self.uvs = [god.assets.get_uvs(tex_name+str(i)) for i in range(frames)] if frames > 0 else None
        self.anim = Anim(frames, frame_speed)
        self.duration = duration
        self.born_time = camera.get_ticks()
        self.destroyed = False
        
    def instantiate(self):
        god.world.add_uparticle(self)
        return self
        
    def update_rect_obj(self):
        if self.rect.colliderect(camera.world_rect) or camera.get_ticks()-god.world.forced_refresh > 990:
            self.rect_obj.update_positions(self.rect.center, None, self.rect.size, self.angle)
        
    def animate(self):
        self.anim.update()
        self.rect_obj.uv = self.uvs[self.anim.get_idx()]
        
    def update(self):
        if self.duration != 0:
            if camera.get_ticks() - self.born_time >= self.duration*1000:
                self.destroy()
        
    def destroy(self):
        if self.destroyed:
            return
        god.world.remove_uparticle(self)
        self.destroyed = True
        
class MovingParticle(Particle):
    def __init__(self, pos, size, dir, dist, speed, tex_name, frames = 0, col=None, frame_speed=0):
        super().__init__(pos, size, tex_name, frames, col, frame_speed)
        self.tex_name = tex_name
        self.dir, self.dist, self.speed = pygame.Vector2(dir), dist, speed
        self.start_pos = pygame.Vector2(pos)
        self.angle = 0
        
    def face_dir(self):
        self.angle = self.dir.as_polar()[1]+90
        #if self.angle-90 < 0:
        #    self.angle = abs(self.angle+90)
        #    self.rect_obj.uv = self.world.assets.get_uvs(self.tex_name, flipx=True)
        
    def move(self):
        self.rect.center += self.dir*self.speed*camera.dt
        self.update_rect_obj()
        if self.start_pos.distance_to(self.rect.center) > self.dist:
            self.destroy()
            
    def update(self):
        self.move()
        
class GrowingParticle(Particle):
    def __init__(self,pos, size, increase, grow_time, disappear_time, tex_name, frames=0, col=None, frame_speed=0):
        super().__init__(pos, size, tex_name, frames, col, frame_speed)
        self.increase, self.grow_time, self.disappear_time = increase, grow_time, disappear_time
        self.start_w, self.start_h = self.rect.w, self.rect.h
        self.start_time = camera.get_ticks()
        self.start_disappear = -1
    
    def grow(self):
        if self.rect.w < self.start_w+self.increase:
            increase = (self.increase*((camera.get_ticks()-self.start_time)/1000))/self.grow_time
            center = self.rect.center
            self.rect.size = (self.start_w+increase, self.start_h+increase)
            self.rect.center = center
            self.update_rect_obj()
        elif self.start_disappear < 0:
            self.start_disappear = camera.get_ticks()
        if self.start_disappear > 0:
            alpha = 1-((camera.get_ticks()-self.start_disappear)/1000)/(self.disappear_time)
            if alpha <= 0:
                self.destroy()
            self.rect_obj.color = (self.rect_obj.color[0], self.rect_obj.color[1], self.rect_obj.color[2], alpha)
            
    def update(self):
        self.grow()
        
class GrowingParticleY(Particle):
    def __init__(self, pos, size, increase, grow_time, disappear_time, tex_name, frames=0, col=None, frame_speed=0):
        super().__init__(pos, size, tex_name, frames, col, frame_speed)
        self.increase, self.grow_time, self.disappear_time = increase, grow_time, disappear_time
        self.start_h = self.rect.h
        self.start_time = camera.get_ticks()
        self.start_disappear = -1
    
    def grow(self):
        if self.rect.h < self.start_h+self.increase:
            increase = (self.increase*((camera.get_ticks()-self.start_time)/1000))/self.grow_time
            center = self.rect.midbottom
            self.rect.h = self.start_h+increase
            self.rect.midbottom = center
            self.update_rect_obj()
        elif self.start_disappear < 0:
            self.start_disappear = camera.get_ticks()
        if self.start_disappear > 0:
            alpha = 1-((camera.get_ticks()-self.start_disappear)/1000)/(self.disappear_time)
            if alpha <= 0:
                self.destroy()
            self.rect_obj.color = (self.rect_obj.color[0], self.rect_obj.color[1], self.rect_obj.color[2], alpha)
            
    def update(self):
        self.grow()
        
class Proj(MovingParticle):
    def __init__(self, pos, size, dir, tree, proj, attrs=None, invis_enemies=None):
        super().__init__(pos, size, dir, proj["dist"], proj["speed"], proj["tex_name"], proj.get("frames", 0), proj.get("color", WHITE), proj.get("frame_speed", 0))
        self.tree, self.attrs, self.invis_enemies = tree, (attrs if attrs else {}), (invis_enemies if invis_enemies else [])
        self.proj = proj
        self.face_dir()
        
    def update(self):
        self.move()
        for enemy in god.world.enemies:
            if enemy not in self.invis_enemies:
                if self.rect.colliderect(enemy.rect):
                    self.destroy()
                    enemy.damage(self.proj["damage"])
                    self.tree.attacker.hit(enemy, self)
                    break
        