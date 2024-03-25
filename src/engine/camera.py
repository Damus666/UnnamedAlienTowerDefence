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
desired_fps: float = 0
proj_size: float = 1
dt: float = 0
unit: float = 0
position: pygame.Vector2 = pygame.Vector2()
zoom: float = 0.5

def init_window(w: int, h: int, title: str, fps: float = 0, proj_scale: float = 1, extra_flags: int = 0):
    global screen_surf, win_w, win_h, clock, desired_fps, proj_size, win_center
    screen_surf = pygame.display.set_mode((w, h), pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF | extra_flags)
    win_w, win_h = screen_surf.get_size()
    clock = pygame.Clock()
    desired_fps = fps
    proj_size = proj_scale
    win_center = pygame.Vector2(win_w//2, win_h//2)
    pygame.display.set_caption(title)
    
    make_proj()
    update_view()
    
def window_resized(w: int, h: int):
    global win_w, win_h, win_center
    win_w, win_h = w, h
    win_center = pygame.Vector2(win_w//2, win_h//2)
    make_proj()

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
        
screen_mouse: pygame.Vector2 = pygame.Vector2()
ui_mouse: pygame.Vector2 = pygame.Vector2()
world_mouse: pygame.Vector2 = pygame.Vector2()
rect = pygame.FRect(0, 0, 0, 0)
ui_rect = pygame.FRect(0, 0, 0, 0)
        
def update_view():
    global view_mat4, rect, ui_rect
    view_mat4 = glm.translate(glm.vec3(-position.x, -position.y, 0))
    ui_rect = pygame.FRect(-win_w/unit, -win_h/unit, (win_w/unit)*2, (win_h/unit)*2)
    rect = pygame.FRect(screen_to_world(pygame.Vector2(0, 0)), (ui_rect.w/zoom, ui_rect.h/zoom))
    
def update_mouse():
    global screen_mouse, ui_mouse, world_mouse
    screen_mouse = pygame.Vector2(pygame.mouse.get_pos())
    ui_mouse = screen_to_ui(screen_mouse)
    world_mouse = screen_to_world(screen_mouse)
    
def tick_window():
    global dt
    pygame.display.flip()
    dt = min(clock.tick(desired_fps)/1000, 0.3)
    
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
    