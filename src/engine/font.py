import moderngl
import pygame
import string

from .buffer import RectObj
from .texture import SpriteAtlas

def add_font(name, pg_font: pygame.Font, atlas: SpriteAtlas, tex_id, antialiasing=True, base_scale=1, 
             extra_chars="", hebrew_chars="", hebrew_font: pygame.Font=None, arabic_chars="", arabic_font: pygame.Font=None):
    chars = string.ascii_letters+string.digits+string.punctuation+" "+extra_chars
    bitmaps[name] = FontBitmap(pg_font, chars+hebrew_chars+arabic_chars, tex_id, atlas, base_scale)
    for char in chars:
        atlas.add(pg_font.render(char, antialiasing, "white"), f"{name}_{char}")
    for char in hebrew_chars:
        atlas.add(hebrew_font.render(char, antialiasing, "white"), f"{name}_{char}")
    for char in arabic_chars:
        atlas.add(arabic_font.render(char, antialiasing, "white"), f"{name}_{char}")

class FontBitmap:
    def __init__(self, pg_font: pygame.Font, chars, tex_id, atlas:SpriteAtlas, base_scale):
        self.height = pg_font.get_height()*base_scale
        self.tex_id = tex_id
        self.atlas = atlas
        self.chars_w = {}
        for char in chars:
            self.chars_w[char] = pg_font.size(char)[0]*base_scale
    
    def char_w(self, char, scale):
        return self.chars_w.get(char, 0)*scale

bitmaps: dict[str, FontBitmap] = {}

def render_single(font_name: str, text: str, position, scale=1, pos_name="center", color=(1,1,1,1)):
    bitmap = bitmaps[font_name]
    x = y = h = 0
    all_chars = []
    for char in text:
        cw = bitmap.char_w(char, scale)
        all_chars.append([char, x, y, cw])
        x += cw
    h = y + bitmap.height*scale
    rect_objs = []
    for char in all_chars:
        if pos_name == "tl":
            char[1] += position[0]
            char[2] += position[1]
        elif pos_name == "center":
            char[1] += position[0]-x/2
            char[2] += position[1]-h/2
        elif pos_name == "tr":
            char[1] += position[0]-x
            char[2] += position[1]
        elif pos_name == "bl":
            char[1] += position[0]
            char[2] += position[1]-h
        elif pos_name == "br":
            char[1] += position[0]-x
            char[2] += position[1]-h
        elif pos_name == "ml":
            char[1] += position[0]
            char[2] += position[1]-h/2

        robj = RectObj(None, (char[1], char[2]), (char[3], bitmap.height*scale), color, bitmap.tex_id,
                       bitmap.atlas.get_uvs(f"{font_name}_{char[0]}"))
        rect_objs.append(robj)
    return rect_objs

def render_single_center(font_name: str, text: str, center, scale=1, color=(1,1,1,1)):
    bitmap = bitmaps[font_name]
    x = y = h = 0
    all_chars = []
    for char in text:
        cw = bitmap.char_w(char, scale)
        all_chars.append([char, x, y, cw])
        x += cw
    h = y + bitmap.height*scale
    rect_objs = []
    for char in all_chars:
        robj = RectObj(None, (char[1]+center[0]-x/2, char[2]+center[1]-h/2), (char[3], bitmap.height*scale), color, bitmap.tex_id,
                       bitmap.atlas.get_uvs(f"{font_name}_{char[0]}"))
        rect_objs.append(robj)
    return rect_objs

def render_full(font_name: str, text: str, position, scale, pos_name="center", max_w=-1, align="center", color=(1, 1, 1, 1)):
    bitmap = bitmaps[font_name]
    x = y = w = h = 0
    chars = []
    lines = []
    all_chars = []
    for char in text:
        cw = bitmap.char_w(char, scale)
        if char == "\n" or (x + cw > max_w and max_w > 0):
            if x > w:
                w = x
            x = 0
            y += bitmap.height*scale
            lines.append(chars)
            all_chars += chars
            chars = []
        if char == "\n":
            continue
        chars.append([char, x, y, cw])
        x += cw
    if x > w:
        w = x
    if len(chars) > 0:
        all_chars += chars
        lines.append(chars)
    h = y + bitmap.height*scale
    if align == "center":
        for line in lines:
            lw = sum([c[3] for c in line])
            offset = w/2-lw/2
            for c in line:
                c[1] += offset
    elif align == "right":
        for line in lines:
            lw = sum([c[3] for c in line])
            offset = w-lw
            for c in line:
                c[1] += offset
    rect_objs = []
    for char in all_chars:
        if pos_name == "tl":
            char[1] += position[0]
            char[2] += position[1]
        elif pos_name == "center":
            char[1] += position[0]-w/2
            char[2] += position[1]-h/2
        elif pos_name == "tr":
            char[1] += position[0]-w
            char[2] += position[1]
        elif pos_name == "bl":
            char[1] += position[0]
            char[2] += position[1]-h
        elif pos_name == "br":
            char[1] += position[0]-w
            char[2] += position[1]-h
        elif pos_name == "ml":
            char[1] += position[0]
            char[2] += position[1]-h/2

        robj = RectObj(None, (char[1], char[2]), (char[3], bitmap.height*scale), color, bitmap.tex_id,
                       bitmap.atlas.get_uvs(f"{font_name}_{char[0]}"))
        rect_objs.append(robj)
    return rect_objs
