from .engine.prelude import *

from .consts import *
from . import god

class ProgressBar:
    def __init__(self, size, corner, maxv, topleft, fill_col, bg_col=BLACK, border_col=BAR_OUTLINE, outline="v", center=None):
        self.size, self.corner, self.maxv, self.topleft, self.fill_col, self.bg_col, self.border_col = (
            size, corner, maxv, topleft, fill_col, bg_col, border_col)
        if center is not None:
            self.topleft = topleft = (center[0]-size[0]/2, center[1]-size[1]/2)
        self.center = (topleft[0]+size[0]/2, topleft[1]+size[1]/2)
        self.bg_rect_objs = panel_rect_objs(size, corner, topleft, self.bg_col)
        self.border_rect_objs = panel_outline_rect_objs(size, corner, topleft, self.border_col, outline)
        self.set_value(maxv)

    def set_value(self, val, maxv = None):
        if val < 0:
            val = 0
        if maxv is not None:
            self.maxv = maxv
        self.val = val
        self.fill_rect_objs = panel_rect_objs((self.size[0]*(val/self.maxv), self.size[1]),
                                               self.corner, self.topleft, self.fill_col, True)

    def get_rect_objs(self):
        return self.bg_rect_objs+self.fill_rect_objs+self.border_rect_objs
    
    @staticmethod
    def runtime_rect_objs(size, corner, val, maxv, center, fill_col, bg_col, border_col=BAR_OUTLINE, outline="v"):
        topleft = (center[0]-size[0]/2, center[1]-size[1]/2)
        return (panel_rect_objs(size, corner, topleft, bg_col)+
                panel_rect_objs((size[0]*(val/maxv), size[1]),
                                               corner, topleft, fill_col, True)+
                panel_outline_rect_objs(size, corner, topleft, border_col, outline))
    
def image(topleft, size, name, col=None, center=None, flipx=False):
    return [RectObj(center, topleft, size, col, UI_ATLAS, god.assets.ui_atlas.get_uvs(name, flipx))]

def button(topleft, size, outline_col, text, text_size, outline="m", center=None):
    if center is not None:
        topleft = (center[0]-size[0]/2, center[1]-size[1]/2)
    else:
        center = (topleft[0]+size[0]/2, topleft[1]+size[1]/2)
    return (
        panel_rect_objs(size, BTN_C, topleft, BTN_BG)
        + panel_outline_rect_objs(size, BTN_C, topleft, outline_col, outline)
        + font.render_single_center(MAIN_FONT, text, center, text_size)
    )
    
def checkbox(center, size, outline_col, on, outline="m"):
    size = (size, size)
    topleft = (center[0]-size[0]/2, center[1]-size[1]/2)
    res = (
        panel_rect_objs(size, BTN_C, topleft, BTN_BG)
        + panel_outline_rect_objs(size, BTN_C, topleft, outline_col, outline)
    )
    if on:
        res += image((center[0]-size[0]/4, center[1]-size[1]/4), (size[0]/2, size[1]/2), "circle")
    return res

def panel_rect_objs(size, c, tl, color=(1, 1, 1, 1), prb=False):
    x, y = tl
    w, h = size
    ui_atlas = god.assets.ui_atlas
    square = ui_atlas.get_uvs("square")
    num = min(w, h)
    prev_c = c
    c = min(c, num/2)
    if prb:
        h = (h*c)/prev_c
    
    return [
        # corners
        RectObj(None, tl, (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_tl")), # tl
        RectObj(None, (x, y+h-c), (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_bl")), # bl
        RectObj(None, (x+w-c, y), (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_tr")), # tr
        RectObj(None, (x+w-c, y+h-c), (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_br")), # br
        # sides
        RectObj(None, (x+c, y), ((w-c-c), c), color, UI_ATLAS, square), # top
        RectObj(None, (x+c, y+h-c), ((w-c-c), c), color, UI_ATLAS, square), # bottom
        RectObj(None, (x, y+c), (c, h-c-c), color, UI_ATLAS, square), # left
        RectObj(None, (x+w-c, y+c), (c, h-c-c), color, UI_ATLAS, square), # right
        # inner
        RectObj(None, (x+c, y+c), ((w-c-c), h-c-c), color, UI_ATLAS, square)
    ]

def panel_outline_rect_objs(size, c, tl, color=(1, 1, 1, 1), outline="v"):
    outline_size = (c*OUTLINE_SIZES[outline])/CIRCLE_RADIUS
    x, y = tl
    w, h = size
    ui_atlas = god.assets.ui_atlas
    square = ui_atlas.get_uvs("square")
    num = min(w, h)
    c = min(c, num/2)
    return [
        # corners
        RectObj(None, tl, (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_{outline}_tl")), # tl
        RectObj(None, (x, y+h-c), (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_{outline}_bl")), # bl
        RectObj(None, (x+w-c, y), (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_{outline}_tr")), # tr
        RectObj(None, (x+w-c, y+h-c), (c, c), color, UI_ATLAS, ui_atlas.get_uvs(f"qc_{outline}_br")), # br
        # sides
        RectObj(None, (x+c, y), (w-c-c, outline_size), color, UI_ATLAS, square), # top
        RectObj(None, (x+c, y+h-outline_size), (w-c-c, outline_size), color, UI_ATLAS, square), # bottom
        RectObj(None, (x, y+c), (outline_size, h-c-c), color, UI_ATLAS, square), # left
        RectObj(None, (x+w-outline_size, y+c), (outline_size, h-c-c), color, UI_ATLAS, square), # right
    ]
