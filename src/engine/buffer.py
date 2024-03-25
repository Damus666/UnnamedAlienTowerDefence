import glm
import moderngl
import pygame
import numpy
from . import ctx

DEFAULT_UV = [
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1)
]

def rect_positions_topleft(tx, ty, sx, sy, a=0):
    if a == 0:
        return [
            (tx, ty),
            (tx + sx, ty),
            (tx, ty + sy),
            (tx + sx, ty + sy)
        ]
    c = (tx+sx/2, ty+sy/2)
    return [
            pygame.Vector2(-sx/2, -sy/2).rotate(a)+c,
            pygame.Vector2(sx/2, -sy/2).rotate(a)+c,
            pygame.Vector2(-sx/2, sy/2).rotate(a)+c,
            pygame.Vector2(sx/2, sy/2).rotate(a)+c
        ]
    
def rect_positions_center(cx, cy, sx, sy, a=0):
    return rect_positions_topleft(cx-sx/2, cy-sy/2, sx, sy, a)
    
def empty_vertices(buffer_data: list, amount):
    buffer_data += [[0, 0, 0, 0, 0, 0, 0, 0, 0,] for _ in range(amount*4)]
    
def rect_indices(amount):
    res = []
    offset = 0
    for _ in range(amount):
        res += [0+offset, 1+offset, 2+offset, 2+offset, 1+offset, 3+offset]
        offset += 4
    return numpy.array(res, dtype=numpy.uint32)

def rect_uvs_sheet(cell_index, cell_width, sheet_width):
    return [
        ((cell_width*cell_index)/sheet_width, 0),
        ((cell_width*cell_index+cell_width)/sheet_width, 0),
        ((cell_width*cell_index)/sheet_width, 1),
        ((cell_width*cell_index+cell_width)/sheet_width, 1)
    ]
    
def rect_uvs_atlas(aw, ah, w, h, x, y):
    return [
        (x/aw, y/ah),
        ((x+w)/aw, y/ah),
        (x/aw, (y+h)/ah),
        ((x+w)/aw, (y+h)/ah),
    ]
    
def uvs_flipx(uvs):
    return [uvs[1], uvs[0], uvs[3], uvs[2]]

class RectObj:
    def __init__(self, center=(0,0), topleft=None, size=(1,1), color=None, tex_id=0, uv=None, angle=0):
        self.update_positions(center, topleft, size, angle)
        self.color = color if color is not None else (1, 1, 1, 1)
        self.tex_id = tex_id
        self.uv = uv if uv is not None else DEFAULT_UV.copy()
    
    def update_positions(self, center=(0,0), topleft=None, size=(1,1), angle=0):
        self.pos = center if center else topleft
        self.positions = (rect_positions_center(center[0], center[1], size[0], size[1], angle)
                          if center is not None else 
                          rect_positions_topleft(topleft[0], topleft[1], size[0], size[1], angle))
        
    def add_vertices(self, buffer_data: list):
        buffer_data += [
            [*self.positions[0], *self.color, *self.uv[0], self.tex_id],
            [*self.positions[1], *self.color, *self.uv[1], self.tex_id],
            [*self.positions[2], *self.color, *self.uv[2], self.tex_id],
            [*self.positions[3], *self.color, *self.uv[3], self.tex_id],
        ]
        
    @staticmethod
    def null():
        return RectObj((0,0), None, (0,0), (0, 0, 0, 0), 0, None)

class FixedRectsBatch:
    def __init__(self, rect_objs: list[RectObj], dynamic: bool = False, amount=None):
        self.rect_objs = rect_objs
        self.rects_amount = len(self.rect_objs) if not amount else amount
        self.dynamic = dynamic
        self.create_buffers()
        
    def get_buffer_data(self):
        buffer_data = []
        for rect in self.rect_objs:
            rect.add_vertices(buffer_data)
        empty_vertices(buffer_data, self.rects_amount-len(self.rect_objs))
        return numpy.array(buffer_data, dtype=numpy.float32)
        
    def create_buffers(self):
        self.ibo = ctx.ctx.buffer(rect_indices(self.rects_amount), dynamic=False)
        self.vbo = ctx.ctx.buffer(self.get_buffer_data() if len(self.rect_objs) > 0 else None, dynamic=self.dynamic, reserve=(self.rects_amount*9*4*4 if len(self.rect_objs) <= 0 else 0))
        return self
        
    def create_vao(self, shader_name, *shader_uniforms):
        self.vao = ctx.ctx.vertex_array(ctx.get_shader(shader_name), [(self.vbo, *shader_uniforms)], index_buffer=self.ibo)
        return self
        
    def update_rects(self, rect_objs: list[RectObj]=None):
        self.rect_objs = rect_objs if rect_objs is not None else self.rect_objs
        if len(self.rect_objs) > self.rects_amount:
            raise RuntimeError(f"Tried to add more rects to a fixed rect batch. Max size: {self.rects_amount}, attempt: {len(self.rect_objs)}")
        self.vbo.write(self.get_buffer_data())
        
    def free_rect_objs(self):
        self.rect_objs = []
        
    def render(self):
        self.vao.render()
        
class GrowingRectsBatch:
    def __init__(self, shader_name, *shader_uniforms):
        self.shader_name, self.shader_uniforms = shader_name, shader_uniforms
        self.rect_objs: list[RectObj] = []
        self.reserved_amount = 5
        self.ibo = ctx.ctx.buffer(rect_indices(self.reserved_amount), dynamic=False)
        self.vbo = ctx.ctx.buffer(reserve=self.reserved_amount*9*4*4, dynamic=False)
        self.vao = ctx.ctx.vertex_array(ctx.get_shader(shader_name), [(self.vbo, *shader_uniforms)], index_buffer=self.ibo)
        self.update_rects()
        
    def update_rects(self, rect_objs: list[RectObj]=None):
        self.rect_objs = rect_objs if rect_objs else self.rect_objs
        if len(self.rect_objs) > self.reserved_amount:
            self.reserved_amount = len(self.rect_objs)+5
            self.ibo = ctx.ctx.buffer(rect_indices(self.reserved_amount), dynamic=False)
            self.vbo = ctx.ctx.buffer(reserve=self.reserved_amount*9*4*4, dynamic=False)
            self.vao = ctx.ctx.vertex_array(ctx.get_shader(self.shader_name), [(self.vbo, *self.shader_uniforms)], index_buffer=self.ibo)
        buffer_data = []
        for rect in self.rect_objs:
            rect.add_vertices(buffer_data)
        empty_vertices(buffer_data, self.reserved_amount-len(self.rect_objs))
        buffer_data = numpy.array(buffer_data, dtype=numpy.float32)
        self.vbo.write(buffer_data)
        
    def render(self):
        self.vao.render()
        
    def free_rect_objs(self):
        self.rect_objs = []
