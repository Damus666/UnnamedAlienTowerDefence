import pygame

from . import camera

class Anim:
    def __init__(self, count, speed):
        self.count = count
        self.speed = speed
        self.index = 0
        
    def update(self):
        self.index += self.speed*camera.dt
        if self.index >= self.count:
            self.index = 0
        
    def get_idx(self):
        return int(self.index)
    