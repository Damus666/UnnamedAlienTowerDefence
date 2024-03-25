import moderngl
import pygame
import pathlib
import numpy
import random
from . import ctx, buffer

class Texture:
    def __init__(self, size: tuple[int, int], data: bytes, name: str = "unnamed"):
        self.size: tuple[int, int] = size
        self.data: bytes = data
        self.name: str = name
        self.texture: moderngl.Texture = ctx.ctx.texture(size, 4, data)
        self.ID: int = id(self.texture)
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.is_array: bool = False
        
    def update(self, data: bytes):
        self.texture.write(data)
        self.data = data
        
    def to_surface(self) -> pygame.Surface:
        return pygame.image.frombuffer(self.texture.read(), self.size, "RGBA")
    
    def use(self, location: int):
        self.texture.use(location)
    
    @staticmethod
    def from_surface(surface: pygame.Surface, name: str = "unnamed") -> "Texture":
        return Texture(surface.get_size(), pygame.image.tobytes(surface, "RGBA"), name)
    
    @staticmethod
    def load(filepath: str, name: str|None = None, flipx: bool = False, flipy: bool = False) -> "Texture":
        return Texture.from_surface(pygame.transform.flip(pygame.image.load(filepath).convert_alpha(), flipx, flipy), name if name else pathlib.Path(filepath).stem)
    
class TextureArray:
    def __init__(self, textures: list[Texture], name="unnamed array"):
        self.textures: list[Texture] = list(textures)
        self.tex_index: int = 0
        self.ID = id(self)
        self.name = name
        self.is_array: bool = True
        
    def add_texture(self, texture: Texture):
        self.textures.append(texture)
        
    def set_idx(self, index):
        self.tex_index = index
        
    def use(self, location: int):
        self.textures[self.tex_index].use(location)
    
class TextureBatch:    
    def __init__(self, textures: list[Texture|TextureArray]):
        self.textures: list[Texture|TextureArray] = list(textures)
        self.id_locations: dict[int, int] = {texture.ID:i for i, texture in enumerate(textures)}
        self.names_locations: dict[str, int] = {texture.name:i for i, texture in enumerate(textures)}
        
    def add_texture(self, texture: Texture|TextureArray):
        self.textures.append(texture)
        self.id_locations[texture.ID] = len(self.textures)-1
        self.names_locations[texture.name] = len(self.textures)-1
        
    def get_location(self, texture_name: str) -> int:
        return self.names_locations[texture_name]
            
    def get_id_location(self, texture: Texture|TextureArray) -> int:
        return self.id_locations[texture.ID]
        
    def use(self):
        for i, tex in enumerate(self.textures):
            tex.use(i)
        
    @staticmethod
    def upload_samplers(size: int, uniform_name: str, *shader_names: str, ):
        data = numpy.array(list(range(size)), dtype=numpy.int32)
        for shader_name in shader_names:
            ctx.get_shader(shader_name)[uniform_name].write(data)

class Spritesheet:
    def __init__(self, name):
        self.name = name
        self.surfaces = []
        
    def add(self, surface, name):
        self.cell_width = surface.get_width()
        self.height = surface.get_height()
        self.surfaces.append([surface, name])
        
    def get_idx(self, name):
        return self.surfaces_name_idx[name]
    
    def get_uvs(self, name):
        return buffer.rect_uvs_sheet(self.surfaces_name_idx[name], self.cell_width, self.width)
    
    def get_flipx_uvs(self, name):
        return buffer.uvs_flipx(buffer.rect_uvs_sheet(self.surfaces_name_idx[name], self.cell_width, self.width))
    
    def get_random_name(self):
        return random.choice(list(self.surfaces_name_idx.keys()))
        
    def build(self):
        self.width = (self.cell_width*len(self.surfaces))
        self.sheet_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.sheet_surf.fill(0)
        self.surfaces_name_idx = {}
        for i, (surf, surf_name) in enumerate(self.surfaces):
            self.surfaces_name_idx[surf_name] = i
            self.sheet_surf.blit(surf, (i*self.cell_width, 0))
        self.texture = Texture.from_surface(self.sheet_surf, self.name)
        
class SpriteAtlas:
    def __init__(self):
        self.surfaces: dict[str, pygame.Surface] = {}
        self.uvs: dict[str] = {}
        
    def add(self, surface: pygame.Surface, name: str):
        self.surfaces[name] = surface
        
    def get_uvs(self, name: str, flipx=False):
        return buffer.uvs_flipx(self.uvs[name]) if flipx else self.uvs[name]
            
    def build(self, name):
        surfs = sorted(list(self.surfaces.values()), key= lambda surf: surf.get_height(), reverse=True)
        inv_surfs = {id(surf):name for name, surf in self.surfaces.items()}
        self.height = int(surfs[0].get_width()*2)
        positions = []
        x = y = bw = 0
        for surf in surfs:
            w, h = surf.get_size()
            if self.height-y < h:
                y = 0
                x += bw+1
                bw = 0
            if w > bw:
                bw = w
            positions.append([surf, w, h, x, y])
            y += h+1
        self.width = x+bw
        main_surf = pygame.Surface((self.width, int(self.height*1.1)), pygame.SRCALPHA)
        main_surf.fill(0)
        for surf, w, h, x, y in positions:
            self.uvs[inv_surfs[id(surf)]] = buffer.rect_uvs_atlas(self.width, int(self.height*1.1), w, h, x, y)
            main_surf.blit(surf, (x, y))
        pygame.image.save(main_surf, f"stuff/{name}.png")
        self.texture = Texture.from_surface(main_surf, name)
