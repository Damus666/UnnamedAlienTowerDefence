import pygame.freetype
from .engine.prelude import *

from .consts import *
from . import god
from . import ui

class ShopUI:
    def __init__(self):
        self.is_open = False
        self.ui_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        
        self.trees_rects = {}
        self.buildings_rects = {}
        
        self.hovered_trees = []
        self.hovered_buildings = []
        
        self.build()
                        
    def update(self):
        if not self.is_open:
            return
        
        for name, rect in self.trees_rects.items():
            if rect.collidepoint(camera.ui_mouse):
                can = god.player.level >= TreeData.get(name).unlock_level and god.player.can_buy(TreeData.get(name).price)
                if name not in self.hovered_trees:
                    if can:
                        self.hovered_trees.append(name)
                        self.build()
                if can and god.settings.binds["ui_click"].check_frame():
                    self.close()
                    god.player.start_planting(TreeData.get(name))
            else:
                if name in self.hovered_trees:
                    self.hovered_trees.remove(name)
                    self.build()
                    
        for name, rect in self.buildings_rects.items():
            if rect.collidepoint(camera.ui_mouse):
                can = god.player.can_buy(BuildingData.get(name).price)
                if name not in self.hovered_buildings:
                    if can:
                        self.hovered_buildings.append(name)
                        self.build()
                if can and god.settings.binds["ui_click"].check_frame():
                    self.close()
                    god.player.start_building(BuildingData.get(name))
            else:
                if name in self.hovered_buildings:
                    self.hovered_buildings.remove(name)
                    self.build()
            
        
    def build(self):
        rects = []
        
        trees_amount = len(TreeData.get_all())
        total_w = SHOP_CARD_W*trees_amount+CARD_S*trees_amount
        x = -total_w/2
        y = -SHOP_CARD_W-CARD_S
        
        rects += font.render_single_center(MAIN_FONT, f"{god.lang["shop"]}", (0, y-CARD_S*6), 3.2)
        
        for tree in sorted(TreeData.get_all(), key=lambda tree: tree.unlock_level):
            unlocked = god.player.level >= tree.unlock_level
            hovered = tree.name in self.hovered_trees
            
            rects += ui.panel_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), CARD_BG)
            rects += ui.panel_outline_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), UNHOVER_OUTLINE if not hovered else HOVER_OUTLINE)
            rects += ui.image(None, (SHOP_CARD_W/1.8, SHOP_CARD_W/1.8), tree.tex_name, WHITE if unlocked else LOCKED_IMG_COL,
                              (x+SHOP_CARD_W/2, y+SHOP_CARD_W/2))
            if not unlocked:
                rects += font.render_single_center(MAIN_FONT, f"{god.lang["level"]} {tree.unlock_level}", (x+SHOP_CARD_W/2, y+SHOP_CARD_W/2), 1.5)
            else:
                rects += font.render_single_center(MAIN_FONT, f"{tree.price}{god.lang["currency"]}", (x+SHOP_CARD_W/2, y+SHOP_CARD_W-CARD_S*2.2), 1.5, MONEY_COL)
                
            self.trees_rects[tree.name] = pygame.FRect(x, y, SHOP_CARD_W, SHOP_CARD_W)
            x += SHOP_CARD_W+CARD_S
        
        buildings_amount = len(BuildingData.get_all())
        total_w = SHOP_CARD_W*buildings_amount+CARD_S*buildings_amount
        x = -total_w/2
        y = CARD_S
        for building in sorted(BuildingData.get_all(), key=lambda b: b.price):
            hovered = building.name in self.hovered_buildings
            
            rects += ui.panel_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), CARD_BG)
            rects += ui.panel_outline_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), UNHOVER_OUTLINE if not hovered else HOVER_OUTLINE)
            rects += ui.image(None, (SHOP_CARD_W/1.8, SHOP_CARD_W/1.8), building.tex_name, WHITE,
                              (x+SHOP_CARD_W/2, y+SHOP_CARD_W/2))
            rects += font.render_single_center(MAIN_FONT, f"{building.price}{god.lang["currency"]}", (x+SHOP_CARD_W/2, y+SHOP_CARD_W-CARD_S*2.2), 1.5, MONEY_COL)

            self.buildings_rects[building.name] = pygame.FRect(x, y, SHOP_CARD_W, SHOP_CARD_W)
            x += SHOP_CARD_W+CARD_S
        
        self.ui_batch.update_rects(rects)
        
    def render(self):
        self.ui_batch.render()
        
    def toggle(self):
        self.is_open = not self.is_open
        
    def close(self):
        self.is_open = False
