from .engine.prelude import *
import os
import json

from .consts import *
from . import god

class KC:
    def __init__(self, code, type="key"):
        self.type, self.code = type, code

    def check_event(self, event: pygame.Event):
        if self.type == "key":
            if event.type == pygame.KEYDOWN:
                if event.key == self.code:
                    return True
        elif self.type == "mouse":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == self.code:
                    return True
        return False
    
    def check_frame(self):
        if self.type == "key":
            return camera.keys[self.code]
        elif self.type == "mouse":
            return camera.buttons[self.code-1]

class Keybind:
    def __init__(self, bind:KC, *alts:KC):
        self.bind, self.alts = bind, list(alts)

    def check_event(self, event: pygame.Event):
        if self.bind.check_event(event):
            return True
        for alt in self.alts:
            if alt.check_event(event):
                return True
        return False
    
    def check_frame(self): 
        if self.bind.check_frame():
            return True
        for alt in self.alts:
            if alt.check_frame():
                return True
        return False
    
class Languages:
    def __init__(self):
        self.langs = {}
        for file in os.listdir(f"assets/languages"):
            with open(f"assets/languages/{file}", "rb") as lfile:
                self.langs[file.split(".")[0]] = json.load(lfile,)
                
    def names(self):
        return list(self.langs.keys())
                
    def get(self, name) -> str:
        res = self.langs[god.settings.lang][name]
        if god.settings.lang in ["heb", "ar"]:
            return res[::-1]
        return res
    
    def __getitem__(self, name):
        return self.get(name)
    
class Tutorial:
    def __init__(self):
        self.complete = False
        self.stage = 1
        self.stage_num = 5
        self.unlocked = [ENERGY_SOURCE]
        self.plants_unlock_stage = 5
        self.complete_time = -9999
        
    def unlocked_building(self, name):
        if self.complete:
            return True
        return name in self.unlocked
    
    def unlocked_plant(self):
        if self.complete:
            return True
        return self.stage >= self.plants_unlock_stage
    
    def placed_building(self, name):
        if self.complete:
            return
        if name == ENERGY_SOURCE and self.stage == 1:
            self.unlocked.append(ENERGY_DISTRIBUTOR)
            self.advance()
        elif name == ENERGY_DISTRIBUTOR and self.stage == 2:
            self.unlocked.append(MINER)
            self.advance()
        elif name == MINER and self.stage == 3:
            self.unlocked.append(BOT)
            self.advance()
        elif name == BOT and self.stage == 4:
            self.advance()
            
    def placed_plant(self):
        self.advance()
        
    def skip(self):
        if self.complete:
            return
        if self.stage == 1:
            self.unlocked.append(ENERGY_DISTRIBUTOR)
        elif self.stage == 2:
            self.unlocked.append(MINER)
        elif self.stage == 3:
            self.unlocked.append(BOT)
        self.advance()
            
    def advance(self):
        if self.complete:
            return
        self.stage += 1
        if self.stage > self.stage_num:
            self.complete = True
            self.complete_time = pygame.time.get_ticks()
            god.sounds.play("level_up")
            god.player.celebrate()
        god.world.ui.build()

class Settings:
    pref_path = None
    user_path = None
    
    def __init__(self):
        self.fps = FPS
        self.fps_counter = True
        self.confetti = True
        self.scaled_mul = 1
        self.ui_high_res = True
        self.max_lights = MAX_LIGHTS 
        self.lang = PREF_LANGUAGE if PREF_LANGUAGE in god.lang.langs.keys() else DEFAULT_LANGUAGE
        self.music_vol = 1
        self.fx_vol = 1
        self.binds: dict[str, Keybind] = {
            "left": Keybind(KC(pygame.K_a), KC(pygame.K_LEFT)),
            "right": Keybind(KC(pygame.K_d), KC(pygame.K_RIGHT)),
            "up": Keybind(KC(pygame.K_w), KC(pygame.K_UP)),
            "down": Keybind(KC(pygame.K_s), KC(pygame.K_DOWN)),
            "shop": Keybind(KC(pygame.K_TAB)),
            "pause": Keybind(KC(pygame.K_ESCAPE)),
            "tree_range": Keybind(KC(pygame.K_t)),
            "cancel_action": Keybind(KC(pygame.K_ESCAPE)),
            "destroy_mode": Keybind(KC(pygame.K_BACKSPACE), KC(pygame.K_DELETE)),
            "place": Keybind(KC(pygame.BUTTON_LEFT, "mouse")),
            "ui_click": Keybind(KC(pygame.BUTTON_LEFT, "mouse")),
        }
        self.save("default_settings")
        self.load()
        self.tutorial = Tutorial()

    def load(self, filename="settings"):
        if os.path.exists(f"{Settings.user_path}{filename}.json"):
            with open(f"{Settings.user_path}{filename}.json", "r") as file:
                data = json.load(file)
                for name in ["fps", "fps_counter", "scaled_mul", "ui_high_res", "max_lights", "lang", "music_vol", "fx_vol", "confetti"]:
                    setattr(self, name, data[name])
                for name, kb_data in data["binds"].items():
                    self.binds[name] = Keybind(KC(kb_data["main"]["code"], kb_data["main"]["type"]),
                                            *[KC(alt_data["code"], alt_data["type"]) for alt_data in kb_data["alts"]])

    def save(self, filename="settings"):
        with open(f"{Settings.user_path}{filename}.json", "w") as file:
            data = {
                name: getattr(self, name) for name in ["fps", "fps_counter", "scaled_mul", "ui_high_res", "max_lights", "lang", "music_vol", "fx_vol", "confetti"]
            }
            data["binds"] = {name: {
                                        "main": {"code": kb.bind.code, "type": kb.bind.type}, 
                                        "alts": [
                                            {"code": alt.code, "type": alt.type} 
                                                 for alt in kb.alts]}
                             for name, kb in self.binds.items()}
            json.dump(data, file)
            
    def reset_settings(self):
        self.load("default_settings")
            
    @staticmethod
    def del_settings():
        if os.path.exists(f"{Settings.user_path}settings.json"):
            os.remove(Settings.user_path+"settings.json")
    
    @staticmethod
    def get_user_path():
        pref_path = pygame.system.get_pref_path(ORG, APP)
        os.makedirs(pref_path+"userdata/", exist_ok=True)
        Settings.pref_path = pref_path
        Settings.user_path = pref_path+"userdata\\"

    def __getitem__(self, name):
        return getattr(self, name)
    
    def __setitem__(self, name, val):
        setattr(self, name, val)
