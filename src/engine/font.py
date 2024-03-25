import moderngl
import pygame

from .texture import Texture, TextureBatch
from . import buffer

font_textures: list[Texture] = []

class FontBitmap:
    def __init__(self, name, pg_font: pygame.Font, chars, antialiasing):
        self.name = name
        self.pg_font = pg_font
        self.chars = chars
        self.antialiasing = antialiasing
        self.pg_surf = self.pg_font.render(self.chars, self.antialiasing, "white")
        self.height = self.pg_font.get_height()
        self.chars_size = self.pg_surf.get_width()
        self.chars_idx = {c:i for i, c in enumerate(self.chars)}
        self.chars_uvs = {}
        self.chars_w = {}
        for c in self.chars:
            i = self.chars_idx[c]
            firstpart = self.chars[0:i]
            startlen = self.pg_font.size(firstpart)[0]
            charlen = self.pg_font.size(c)[0]
            self.chars_uvs[c] = [
                ((startlen)/self.chars_size, 0),
                ((startlen+charlen)/self.chars_size, 0),
                ((startlen)/self.chars_size, 1),
                ((startlen+charlen)/self.chars_size, 1)
            ]
            self.chars_w[c] = charlen
        self.texture = Texture.from_surface(self.pg_surf, self.name)
        self.batch_location = len(font_textures)
        font_textures.append(self.texture)
        
    def scaled_size(self, text, scale_mul):
        size = self.pg_font.size(text)
        return (size[0]*scale_mul, size[1]*scale_mul)
        
font_bitmaps: dict = {}

def add_font(name, pg_font, chars, antialiasing=True):
    global font_bitmaps
    font_bitmaps[name] = FontBitmap(name, pg_font, chars, antialiasing)
    
class TopleftPosBuilder:
    def __init__(self, pos):
        self.pos = pos
    
    def get(self, bitmap: FontBitmap, text: str, size_mul: float):
        ...
        
class FromCenter(TopleftPosBuilder):
    def get(self, bitmap: FontBitmap, text: str, size_mul: float):
        size = bitmap.scaled_size(text, size_mul)
        return (self.pos[0]-size[0]/2, self.pos[1]-size[1]/2)
    
class FromBottomRight(TopleftPosBuilder):
    def get(self, bitmap: FontBitmap, text: str, size_mul: float):
        size = bitmap.scaled_size(text, size_mul)
        return (self.pos[0]-size[0], self.pos[1]-size[1])
    
class FromBottomLeft(TopleftPosBuilder):
    def get(self, bitmap: FontBitmap, text: str, size_mul: float):
        size = bitmap.scaled_size(text, size_mul)
        return (self.pos[0], self.pos[1]-size[1])
    
class FromTopRight(TopleftPosBuilder):
    def get(self, bitmap: FontBitmap, text: str, size_mul: float):
        size = bitmap.scaled_size(text, size_mul)
        return (self.pos[0]-size[0], self.pos[1])
    
class FontBatch:
    def __init__(self, dynamic:bool = False):
        self.text_buffer_data = []
        self.separated_buffer_data = {}
        self.dynamic = dynamic
        self.reserved_size = {}
        
    def set_text(self, index, text: str, color, font_name, size_mul, pos_topleft, other_pos:TopleftPosBuilder=None, reserve=None):
        bitmap: FontBitmap = font_bitmaps[font_name]
        if pos_topleft is None:
            pos_topleft = other_pos.get(bitmap, text, size_mul)
        if index in self.reserved_size:
            text = text.center(self.reserved_size[index], "\t")
        else:
            reserve_size = reserve if reserve else len(text)
            self.reserved_size[index] = reserve_size
            text = text.center(reserve_size, "\t")
        buffer_data = []
        x = pos_topleft[0]
        charh = bitmap.height*size_mul
        for char in text:
            if char == "\t":
                charw = 0
                char_uvs = [(1,1), (1,1), (1,1), (1,1)]
            else:
                charw = bitmap.chars_w[char]*size_mul
                char_uvs = bitmap.chars_uvs[char].copy()
            buffer_data.append([
                buffer.rect_vertices_topleft((x, pos_topleft[1]), (charw, charh)),
                color, bitmap.batch_location, char_uvs
            ])
            x += charw
        self.separated_buffer_data[index] = buffer_data
        
    def clear(self):
        self.text_buffer_data.clear()
        self.separated_buffer_data.clear()
        
    def get_buffer_data(self):
        buffer_data = []
        for bd in self.separated_buffer_data.values():
            buffer_data += bd
        return buffer_data
        
    def make_buffers(self):
        self.vbo, self.ibo = buffer.rects_uvs_vbo_ibo(self.get_buffer_data(), self.dynamic, False)
        
    def update_buffers(self):
        buffer.update_rects_uvs_vbo(self.vbo, self.get_buffer_data())
    