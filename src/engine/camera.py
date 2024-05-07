import glm
import pygame
from . import ctx

proj_mat4 = None
proj_ui_mat4 = None
view_mat4 = None
screen_surf: pygame.Surface = None
win_w: int = 0
win_h: int = 0
win_center: pygame.Vector2 = pygame.Vector2()
clock: pygame.Clock = None
proj_size: float = 1
dt: float = 0
unit: float = 0
position: pygame.Vector2 = pygame.Vector2()
zoom: float = 0.5
time_scale = 1
ticks = 0
pause_time = 0
paused_ticks = 0
screen_mouse: pygame.Vector2 = pygame.Vector2()
ui_mouse: pygame.Vector2 = pygame.Vector2()
world_mouse: pygame.Vector2 = pygame.Vector2()
rect = pygame.FRect(0, 0, 0, 0)
world_rect = pygame.FRect(0, 0, 0, 0)
keys = []
buttons = []

def init_window(w: int, h: int, title: str, proj_scale: float = 1, extra_flags: int = 0, icon=None):
    global screen_surf, win_w, win_h, clock, proj_size, win_center
    pygame.init()
    screen_surf = pygame.display.set_mode((w, h), pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF | extra_flags)
    win_w, win_h = screen_surf.get_size()
    clock = pygame.Clock()
    proj_size = proj_scale
    win_center = pygame.Vector2(win_w//2, win_h//2)
    pygame.display.set_caption(title)
    if icon: pygame.display.set_icon(icon.convert_alpha())
    
    make_proj()
    update_view()
    
def window_resized(w: int, h: int):
    global win_w, win_h, win_center
    win_w, win_h = w, h
    win_center = pygame.Vector2(win_w//2, win_h//2)
    make_proj()
    update_mouse()
    update_view()

def make_proj():
    global proj_mat4, unit, proj_ui_mat4
    ratio = win_w/win_h
    inv_ratio = win_h/win_w
    scaled_size = proj_size/zoom
    if ratio >= inv_ratio:
        proj_mat4 = glm.ortho(-scaled_size*ratio, scaled_size*ratio, scaled_size, -scaled_size, -1000, 1000)
        proj_ui_mat4 = glm.ortho(-proj_size*ratio, proj_size*ratio, proj_size, -proj_size, -1000, 1000)
        unit = win_h/proj_size
    else:
        proj_mat4 = glm.ortho(-scaled_size, scaled_size, scaled_size*inv_ratio, -scaled_size*inv_ratio, -1000, 1000)
        proj_ui_mat4 = glm.ortho(-proj_size, proj_size, proj_size*inv_ratio, -proj_size*inv_ratio, -1000, 1000)
        unit = win_w/proj_size
        
def update_view():
    global view_mat4, rect, world_rect
    view_mat4 = glm.translate(glm.vec3(-position.x, -position.y, 0))
    rect = pygame.FRect(-win_w/unit, -win_h/unit, (win_w/unit)*2, (win_h/unit)*2)
    world_rect = pygame.FRect(screen_to_world(pygame.Vector2(0, 0)), (rect.w/zoom, rect.h/zoom))
    
def update_mouse():
    global screen_mouse, ui_mouse, world_mouse, keys, buttons
    screen_mouse = pygame.Vector2(pygame.mouse.get_pos())
    ui_mouse = screen_to_ui(screen_mouse)
    world_mouse = screen_to_world(screen_mouse)
    keys = pygame.key.get_pressed()
    buttons = pygame.mouse.get_pressed()
    
def tick_window(desired_fps):
    global dt
    pygame.display.flip()
    dt = min(clock.tick(desired_fps)/1000, 0.2)*time_scale
    
def upload_uniforms(*shader_names: str):
    """shader uniforms: proj: mat4, view: mat4"""
    for shader_name in shader_names:
        ctx.shader_writes(shader_name, ("proj", proj_mat4), ("view", view_mat4))
        
def upload_ui_uniforms(*shader_names: str):
    """shader uniforms: projUI: mat4"""
    for shader_name in shader_names:
        ctx.shader_write(shader_name, "projUI", proj_ui_mat4)
        
def mouse_wheel(y, mul, min_, max_):
    global zoom
    zoom = pygame.math.clamp(zoom + (y*mul)*zoom, min_, max_)
    make_proj()
    
def screen_to_world(screen_pos: pygame.Vector2):
    direction = (screen_pos-win_center)/zoom/(unit/2)
    return direction+position

def screen_to_ui(screen_pos: pygame.Vector2):
    return (screen_pos-win_center)/(unit/2)

def pause():
    global time_scale, pause_time
    time_scale = 0
    pause_time = pygame.time.get_ticks()
    
def unpause():
    global time_scale, paused_ticks
    time_scale = 1
    paused_ticks += (pygame.time.get_ticks()-pause_time)
    
def get_ticks():
    if time_scale == 0:
        return pygame.time.get_ticks()-(pygame.time.get_ticks()-pause_time)-paused_ticks
    return pygame.time.get_ticks()-paused_ticks
    