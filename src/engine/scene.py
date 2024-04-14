import pygame
import sys

from . import ctx, camera

class Scene:
    name: str
    
    def __init__(self, manager: "SceneManager", *init_args):
        self.manager = manager
        self.clear_color = (0, 0, 0, 1)
        self.init(*init_args)

    def window_resized(self):
        ...
    
    def init(self, *init_args):
        ...
        
    def update(self):
        ...
        
    def render(self):
        ...
        
    def event(self, event):
        ...
        
    def __init_subclass__(cls) -> None:
        scenes[cls.__name__] = cls
        cls.name = cls.__name__

scenes: dict[str, type] = {}

class SceneManager:        
    def load_scene(self, name, *init_args):
        self.scene: Scene = scenes[name](self, *init_args)
        
    def on_quit(self):
        ...
        
    def quit(self):
        self.on_quit()
        pygame.quit()
        sys.exit()
        
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.VIDEORESIZE:
                    camera.window_resized(event.w, event.h)
                    
                self.scene.event(event)
            
            ctx.clear(self.scene.clear_color) 
            camera.update_mouse()
            camera.update_view()
            self.scene.update()
            self.pre_render()
            self.scene.render()
            self.post_render()

    def pre_render(self):
        ...

    def post_render(self):
        ...
            