import numpy
import pygame
from . import ctx
from .usezen import USE_ZEN

class Light:
    def __init__(self, pos, color, range, intensity):
        self.color, self.range, self.intensity = color, range, intensity
        self.rect = pygame.FRect(0, 0, range*1.6, range*2*1.6)
        self.rect.center = pos
        self.active = True
        if len(self.color) > 3:
            raise RuntimeError(f"Lights must have a color without alpha, not of length {len(self.color)}")
                
    def add_to_uniform(self, uniform_data: list):
        uniform_data += [*self.rect.center, *self.color, self.range, self.intensity]
        
class LightBatch:
    def __init__(self, filter_func=None):
        self.lights: list[Light] = []
        self.filtered: list[Light] = []
        self.filter_func = filter_func
        self.update_buffer()
        
    def update_buffer(self):
        data = []
        for light in self.filtered:
            light.add_to_uniform(data)
        self.buffer = data
        
    def add_light(self, light):
        self.lights.append(light)
        self.filtered.append(light)
        self.update_buffer()
        
    def remove_light(self, light):
        if light in self.lights:
            self.lights.remove(light)
        if light in self.filtered:
            self.filtered.remove(light)
        self.update_buffer()
        
    def filter(self):
        self.filtered = [l for l in self.lights if l.active and self.filter_func(l)]
        self.update_buffer()
        
    @staticmethod
    def upload_uniform(static_batch, dynamic_batch, shader_name, max_lights):
        numlights_data = float(min(len(static_batch.filtered)+len(dynamic_batch.filtered), max_lights))
        data = static_batch.buffer+dynamic_batch.buffer
        lightdata_data = numpy.fromiter(data + [0 for _ in range(max(0, max_lights*7-len(data)))], dtype=numpy.float32)
        if USE_ZEN:
            ctx.shader_set(shader_name, "numLights", numlights_data)
            ctx.shader_set(shader_name, "lightData", lightdata_data)
        else:
            ctx.get_shader(shader_name)["numLights"] = numlights_data
            ctx.get_shader(shader_name)["lightData"] = lightdata_data
