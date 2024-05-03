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
        self.tutorial_complete_rects = (
            ui.panel_rect_objs((camera.rect.w+1, 3.2), 0.5, (-camera.rect.w/2-0.5, -3.2/2), CARD_BG)
            + ui.panel_outline_rect_objs((camera.rect.w+1, 3.2), 0.5, (-camera.rect.w/2-0.5, -3.2/2), UNHOVER_OUTLINE)
            + font.render_single_center(MAIN_FONT, f"{god.lang["tutorial-completed"]}", (0, 0), 4)
        )
        s = 5
        self.level_up_rects = (
            ui.panel_rect_objs((camera.rect.w+1, s), 0.5, (-camera.rect.w/2-0.5, -s/2), CARD_BG)
            + ui.panel_outline_rect_objs((camera.rect.w+1, s), 0.5, (-camera.rect.w/2-0.5, -s/2), UNHOVER_OUTLINE)
            + font.render_single_center(MAIN_FONT, f"{god.lang["level-up"]}", (0, -s/4), 3.4)
            + font.render_single_center(MAIN_FONT, f"{god.player.level-1} -----> {god.player.level}", (0, s/4), 3.6)
        )
        
        self.overlay_bgs = []
        self.overlay_outlines = []
        self.overlay_outlines_hovered = []
        self.overlay_icons = []
        self.overlay_icons_active = []
        self.overlay_rects = []
        self.overlay_rect = pygame.FRect(camera.rect.right-S-OVERLAYBTN_SIZE[0], camera.rect.bottom-S-OVERLAYBTN_SIZE[0]*4-S*4, OVERLAYBTN_SIZE[0]*2, OVERLAYBTN_SIZE[0]*5)
        y = camera.rect.bottom-S
        for name in (["pause", "shop", "destroy", "range", "start_wave"]):
            pos = (camera.rect.right-S-OVERLAYBTN_SIZE[0], y-OVERLAYBTN_SIZE[0])
            innerpos = (pos[0]+OVERLAYBTN_SIZE[0]/2, pos[1]+OVERLAYBTN_SIZE[0]/2)
            self.overlay_bgs.append(ui.image(pos, OVERLAYBTN_SIZE, "circle", BTN_BG))
            self.overlay_outlines.append(ui.image(pos, OVERLAYBTN_SIZE, "co_v", UNHOVER_OUTLINE))
            self.overlay_outlines_hovered.append(ui.image(pos, OVERLAYBTN_SIZE, "co_v", HOVER_OUTLINE))
            self.overlay_icons.append(ui.image(None, OVERLAYINNER_SIZE, name, None, innerpos))
            self.overlay_icons_active.append(ui.image(None, OVERLAYINNER_SIZE, name, (0, 1, 0, 1), innerpos))
            self.overlay_rects.append(pygame.FRect(pos, OVERLAYBTN_SIZE))
            y -= OVERLAYBTN_SIZE[0]+S
            
        if not god.settings.tutorial.complete:
            self.tutorial_rects = []
            self.tutorial_txt_w = font.render_single_width(MAIN_FONT, f"{god.lang["tutorial"]} {god.settings.tutorial.stage}/{god.settings.tutorial.stage_num}", 2)
            txt_rects, txt_w, txt_h = font.render_full(MAIN_FONT, f"{god.lang[f"tutorial_step{god.settings.tutorial.stage}"]}",
                                                          (camera.rect.left+S*4, camera.rect.bottom-S*4), 1.1, "bl", camera.rect.w/4.2, "left")
            c = 0.3
            ph = txt_h+(tt_h:=font.render_single_height(MAIN_FONT, 2))+S*4+c*2
            txt_w = max(txt_w, self.tutorial_txt_w+S*3+2.6)
            self.tutorial_txt_h = tt_h
            self.tutorial_txtb_h = txt_h
            self.tutorial_rects += ui.panel_rect_objs((txt_w+c*2.5, ph), c, (camera.rect.left-c, camera.rect.bottom-ph+c), (0, 0, 0, 0.46))
            self.tutorial_rects += txt_rects
            self.tutorial_rects += font.render_single(MAIN_FONT, f"{god.lang["tutorial"]} {god.settings.tutorial.stage}/{god.settings.tutorial.stage_num}", (
                                                    camera.rect.left+S*4, camera.rect.bottom-S*8-txt_h), 2, "bl")
            self.tutorial_rects += ui.panel_outline_rect_objs((txt_w+c*2.5, ph), c, (camera.rect.left-c, camera.rect.bottom-ph+c), UNHOVER_OUTLINE, "i")
        
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
        if not god.settings.tutorial.complete:
            self.static_top_rects += self.tutorial_rects

    def update(self):
        rects = []
        
        if not god.world.spawner.wave_active:
            # next wave
            next_wave = WAVE_COOLDOWN-((camera.get_ticks()-god.world.spawner.wave_end_time)/1000)
            self.top_bar.set_value(WAVE_COOLDOWN if god.settings.manual_wave else next_wave, WAVE_COOLDOWN)
            rects += self.top_bar.fill_rect_objs
            if god.settings.manual_wave:
                text = f"{god.lang["manual-wave-help"]}"
            else:
                text = f"{god.lang["next-wave"]} {int(next_wave)}{god.lang["second-short"]}"
            if not god.settings.tutorial.complete:
                text = f"{god.lang["finish-or-skip-tutorial"]}"
            rects += font.render_single_center(MAIN_FONT, 
                text,
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
            
        # wrench
        if god.player.destroying and not self.pause.is_open:
            rects += ui.image(None, (1, 1), "wrench", None, camera.ui_mouse, True)
            
        # overlay
        if not self.pause.is_open:
            y = camera.rect.bottom-S
            for i, name in enumerate(["pause", "shop", "destroy", "range", "start_wave"]):
                rects += self.overlay_bgs[i]
                if self.overlay_activity(name):
                    rects += self.overlay_icons_active[i]
                else:
                    rects += self.overlay_icons[i]
                hovered = self.overlay_rects[i].collidepoint(camera.ui_mouse)
                if hovered:
                    rects += self.overlay_outlines_hovered[i]
                else:
                    rects += self.overlay_outlines[i]
        
        if not self.pause.is_open and not self.shop.is_open:
            # wave complete
            if camera.get_ticks() - god.world.spawner.wave_complete_time < EVENT_UI_DURATION*1000:
                rects += self.wave_complete_rects
                
            # level up
            if camera.get_ticks() - god.player.level_up_time < EVENT_UI_DURATION*1000:
                rects += self.level_up_rects
                
            # tutorial completed
            if camera.get_ticks() - god.settings.tutorial.complete_time < EVENT_UI_DURATION*1000:
                rects += self.tutorial_complete_rects
        
        # indicators:
        for ind in list(self.indicators):
            rects += ind.update()

        self.ui_batch.update_rects(rects)
        
        self.update_world()
        self.shop.update()
        self.pause.update()
        
    def event(self, event):
        if self.pause.is_open:
            return
        
        if god.settings.binds["ui_click"].check_event(event):
            for i, rect in enumerate(self.overlay_rects):
                if rect.collidepoint(camera.ui_mouse):
                    getattr(god.player, f"event_{["pause", "shop", "destroy", "range", "start_wave"][i]}")()
                    break
            if self.tutorial_rect.collidepoint(camera.ui_mouse):
                god.settings.tutorial.skip()
                
        if event.type == pygame.MOUSEMOTION:  
            if self.tutorial_rect.collidepoint(camera.ui_mouse):
                if not self.tutorial_hovering:
                    self.tutorial_hovering = True
                    self.update_static()
            else:
                if self.tutorial_hovering:
                    self.tutorial_hovering = False
                    self.update_static()
        
    def overlay_activity(self, name):
        match name:
            case "pause":
                return self.pause.is_open
            case "shop":
                return self.shop.is_open
            case "destroy":
                return god.player.destroying
            case "range":
                return self.tree_range_active
            case "start_wave":
                return god.world.spawner.wave_active
        
    def update_world(self):
        rects = []+god.world.silly_obj
        
        # enemy health bars
        for enemy in god.world.enemies:
            if enemy.health < enemy.enemy.health and camera.world_mouse.distance_to(enemy.rect.center) <= ENEMY_UI_DIST:
                rects.extend(enemy.get_health_rect_objs())
                
        # tree bars    
        for tree in god.world.trees:
            if tree.energy <= 0:
                rects.extend(tree.warning_rect_objs)
            if tree.pos.distance_to(camera.world_mouse) <= TREE_UI_DIST:
                rects.extend(tree.get_bar_rect_objs())
                
        # building ui
        for building in god.world.buildings:
            if building.pos.distance_to(camera.world_mouse) <= TREE_UI_DIST:
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
        
        # ignore tutorial
        if not god.settings.tutorial.complete:
            self.tutorial_rect = pygame.FRect(camera.rect.left+S*8+self.tutorial_txt_w, 
                                              camera.rect.bottom-S*8-self.tutorial_txtb_h-self.tutorial_txt_h+0.1, 2.6, self.tutorial_txt_h-0.2)
            hovered = self.tutorial_rect.collidepoint(camera.ui_mouse)
            self.tutorial_hovering = hovered
            rects += ui.button(self.tutorial_rect.topleft, self.tutorial_rect.size, HOVER_OUTLINE if hovered else UNHOVER_OUTLINE, f"{god.lang["skip"]}", 1.2, "m")

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