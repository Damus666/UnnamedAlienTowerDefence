from .engine.prelude import *
import typing
if typing.TYPE_CHECKING:
    from .world import World

from .consts import *
from .ui import ProgressBar
from .particle import Particle
from .menu_ui import ShopUI, PauseUI
from . import ui
from . import god

class WorldUI:
    def __init__(self):
        self.static_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        self.static_top_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        self.ui_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        self.world_batch = GrowingRectsBatch(UNLIT_SHADER, *SHADER_UNIFORMS)
        
        self.shop = ShopUI()
        self.pause = PauseUI()
        self.indicators = []

        self.build()
        
        self.tree_range_active = False
        self.tree_range_particles: list[Particle] = []
        
    def toggle_tree_range(self):
        if self.tree_range_active:
            self.tree_range_active = False
            for p in self.tree_range_particles:
                p.destroy()
            self.tree_range_particles = []
        else:
            for tree in god.world.trees:
                if tree.tree.has_light:
                    col = (*tree.tree.light_data[0], PREVIW_RANGE_COL[-1])
                else:
                    col = PREVIW_RANGE_COL
                self.tree_range_particles.append(Particle(tree.rect.center, (tree.tree.attack_range*2, tree.tree.attack_range*2), "circle_o", 0, col).instantiate())
            for build in god.world.buildings:
                if build.building.tex_name in ENERGY_TILES:
                    self.tree_range_particles.append(Particle(build.rect.center, (ENERGY_DISTANCE*2, ENERGY_DISTANCE*2), "circle_o", 0, PREVIW_ENERGY_COL).instantiate())
            self.tree_range_active = True

    def build(self):
        self.player_health_bar = ProgressBar((camera.rect.w/TL_BAR_W, PRB_H), PRB_C, god.world.map.health, 
                                             (-camera.rect.w/TL_BAR_O, camera.rect.bottom-PRB_H/2), 
                                             HEALTH_BAR_FILL, HEALTH_BAR_BG, outline="v")
        
        self.top_bar = ProgressBar((camera.rect.w/TL_BAR_W, PRB_H), PRB_C, WAVE_COOLDOWN, (-camera.rect.w/TL_BAR_O, camera.rect.top-PRB_H/2),
                                         (0.5, 0, 0.8, 0.4), (0.4, 0, 0.6, 0.4), outline="v")
        
        self.xp_bar = ProgressBar(((camera.rect.w/TL_BAR_W)*1.2, PRB_H), PRB_C, god.player.next_level_xp*2, None, XP_BAR_FILL, XP_BAR_BG, 
                                  center=(camera.rect.topleft))
        
        self.level_circle_rects = (ui.image((LEVEL_CIRCLE_TL[0]+camera.rect.left, LEVEL_CIRCLE_TL[1]+camera.rect.top), LEVEL_CIRCLE_SIZE, "circle", CARD_BG)
                                +ui.image((LEVEL_CIRCLE_TL[0]+camera.rect.left, LEVEL_CIRCLE_TL[1]+camera.rect.top), LEVEL_CIRCLE_SIZE, "co_b", UNHOVER_OUTLINE))
        
        #self.money_icon_rects = ui.image((camera.rect.left+LEVEL_CIRCLE_SIZE[0]+S*4, LEVEL_CIRCLE_TL[1]+camera.rect.top+S*2), (MONEY_ICON_W, MONEY_ICON_W), "square")
        
        self.damage_overlay = ui.image(camera.rect.topleft, camera.rect.size, DAMAGE_OVERLAY, (1, 1, 1, 1))
        
        self.wave_complete_rects = (
            ui.panel_rect_objs((camera.rect.w+1, 3.2), 0.5, (-camera.rect.w/2-0.5, -3.2/2), CARD_BG)
            + ui.panel_outline_rect_objs((camera.rect.w+1, 3.2), 0.5, (-camera.rect.w/2-0.5, -3.2/2), UNHOVER_OUTLINE)
            + font.render_single_center(MAIN_FONT, f"{god.lang["wave-completed"]}", (0, 0), 4)
        )
        s = 5
        self.level_up_rects = (
            ui.panel_rect_objs((camera.rect.w+1, s), 0.5, (-camera.rect.w/2-0.5, -s/2), CARD_BG)
            + ui.panel_outline_rect_objs((camera.rect.w+1, s), 0.5, (-camera.rect.w/2-0.5, -s/2), UNHOVER_OUTLINE)
            + font.render_single_center(MAIN_FONT, f"{god.lang["level-up"]}", (0, -s/4), 3.4)
            + font.render_single_center(MAIN_FONT, f"{god.player.level-1} -----> {god.player.level}", (0, s/4), 3.6)
        )
        
        self.update_always()
        self.update_static()
        
        self.shop.build()
        self.pause.build()

    def update_always(self):
        self.static_rects = []
        self.static_rects += (self.top_bar.bg_rect_objs
                                +self.player_health_bar.bg_rect_objs
                                +self.xp_bar.bg_rect_objs
                               # +self.money_icon_rects
                            )

        self.static_top_rects = []
        self.static_top_rects += (self.top_bar.border_rect_objs
                                    +self.player_health_bar.border_rect_objs
                                    +self.xp_bar.border_rect_objs
                                    +self.level_circle_rects
                                )

    def update(self):
        rects = []
        
        if not god.world.spawner.wave_active:
            # next wave
            next_wave = WAVE_COOLDOWN-((camera.get_ticks()-god.world.spawner.wave_end_time)/1000)
            self.top_bar.set_value(next_wave, WAVE_COOLDOWN)
            rects += self.top_bar.fill_rect_objs
            rects += font.render_single_center(MAIN_FONT, 
                f"{god.lang["next-wave"]} {int(next_wave)}{god.lang["second-short"]}",
                (0, camera.rect.top+PRB_H/4.2))
        else:
            # enemies in wave
            if self.top_bar.val != god.world.spawner.wave_enemies_amount-god.world.spawner.killed_enemies:
                self.top_bar.set_value(god.world.spawner.wave_enemies_amount-god.world.spawner.killed_enemies, god.world.spawner.wave_enemies_amount)
            rects += self.top_bar.fill_rect_objs
            rects += font.render_single_center(MAIN_FONT, 
                f"{god.lang["enemies-left"]} {int(god.world.spawner.wave_enemies_amount-god.world.spawner.killed_enemies)}/{god.world.spawner.wave_enemies_amount}",
                (0, camera.rect.top+PRB_H/4.2))
        
        # fps counter
        if god.settings.fps_counter:
            rects += font.render_single(MAIN_FONT, f"{camera.clock.get_fps():.1f} FPS ", camera.rect.topright, pos_name="tr")
            
        # damage overlay
        if camera.get_ticks() - god.world.last_damage < DAMAGE_OVERLAY_DURATION*1000:
            alpha = 0.5-((camera.get_ticks() - god.world.last_damage)/(DAMAGE_OVERLAY_DURATION*1000))*0.5
            self.damage_overlay[0].color = (1, 1, 1, alpha)
            self.damage_overlay[0].update_buffer_data()
            rects += self.damage_overlay
        
        # wave complete
        if camera.get_ticks() - god.world.spawner.wave_complete_time < EVENT_UI_DURATION*1000:
            rects += self.wave_complete_rects
            
        # level up
        if camera.get_ticks() - god.player.level_up_time < EVENT_UI_DURATION*1000:
            rects += self.level_up_rects
        
        # indicators:
        for ind in list(self.indicators):
            rects += ind.update()

        self.ui_batch.update_rects(rects)
        
        self.update_world()
        self.shop.update()
        self.pause.update()
        
    def update_world(self):
        rects = []+god.world.silly_obj
        
        # enemy health bars
        for enemy in god.world.enemies:
            if enemy.health < enemy.enemy.health and enemy.rect.colliderect(camera.world_rect):
                rects.extend(enemy.get_health_rect_objs())
                
        # tree bars    
        for tree in god.world.trees:
            if tree.rect.colliderect(camera.world_rect):
                rects.extend(tree.get_bar_rect_objs())
                
        # building ui
        for building in god.world.buildings:
            if building.rect.colliderect(camera.world_rect):
                rects.extend(building.get_ui_rect_objs())
                    
        self.world_batch.update_rects(rects)

    def update_static(self):
        # bottom
        rects = []
        rects += self.static_rects
        
        # health bar
        if self.player_health_bar.val != god.world.health:
            self.player_health_bar.set_value(god.world.health, god.world.map.health)
        rects += self.player_health_bar.fill_rect_objs    

        # xp bar
        if self.xp_bar.val != god.player.xp+god.player.next_level_xp:
            self.xp_bar.set_value(god.player.xp+god.player.next_level_xp, god.player.next_level_xp*2)
        rects += self.xp_bar.fill_rect_objs

        self.static_batch.update_rects(rects)

        # top
        rects = []
        rects += self.static_top_rects

        # wave counter
        extra = 1 if god.world.spawner.wave_active else 0
        rects += font.render_single_center(MAIN_FONT, f"{god.lang["wave"]} {god.world.spawner.wave_idx+extra}/{god.world.spawner.waves_amount}", 
                                           (0, camera.rect.top+PRB_H/1.2))
        
        # level
        rects += font.render_single_center(MAIN_FONT, f"{god.player.level}", 
                                           (LEVEL_CIRCLE_TL[0]+LEVEL_CIRCLE_SIZE[0]/2+camera.rect.x, LEVEL_CIRCLE_TL[1]+LEVEL_CIRCLE_SIZE[0]/2+camera.rect.y), 2)

        # health
        rects += font.render_single_center(MAIN_FONT, f"{int(god.world.health)}/{god.world.map.health}", 
                                           (0, camera.rect.bottom-PRB_H/4), )
        
        # money
        rects += font.render_single(MAIN_FONT, f"{int(god.player.money)}{god.lang["currency"]}", (camera.rect.left+LEVEL_CIRCLE_SIZE[0]+S*5, LEVEL_CIRCLE_TL[1]+camera.rect.top+S*2+MONEY_ICON_W/2), 
                                    1.4, "ml", MONEY_COL)

        self.static_top_batch.update_rects(rects) 

    def render(self):
        self.world_batch.render()
        self.static_batch.render()
        self.ui_batch.render()
        self.static_top_batch.render()
        if self.shop.is_open:
            self.shop.render()
        if self.pause.is_open:
            self.pause.render()