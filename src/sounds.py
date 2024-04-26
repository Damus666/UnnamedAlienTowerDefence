from .engine.prelude import *
import random
import os

from .consts import *
from . import god

class Sounds:
    @staticmethod
    def pre_init():
        pygame.mixer.pre_init(buffer=40496, allowedchanges=pygame.AUDIO_ALLOW_ANY_CHANGE)
    
    def __init__(self):        
        sound_assets: list[SoundAsset] = [
            single("hover", 0.9),
            single("click", 1),
            single("hurt", 1),
            single("explosion", 0.5),
            single("level_up", 1),
            single("bubbles", 0.7),
            single("upgrade", 0.5),
            single("money", 0.8),
            single("win", 1),
            single("next_wave", 1),
            single("tree_place", 0.8),
            single("alien", 0.6),
            single("ore", 0.4),
            single("roar", 0.8),
            
            folder("building_place", 0.7),
            folder("hit", 0.5),
            folder("attack", 0.5)
        ]
        
        self.sounds: dict[str, SoundAsset] = {sa.name: sa for sa in sound_assets}
        self.update_volumes()
        
    def play(self, name, stop=True):
        if stop:
            self.sounds[name].stop()
        self.sounds[name].play()
        
    def play_random(self, name, stop=True):
        if stop:
            self.sounds[name].stop()
        self.sounds[name].play_random()
        
    def music_play(self, name):
        pygame.mixer_music.unload()
        pygame.mixer_music.load(f"assets/sounds/{name}.wav")
        pygame.mixer_music.play(-1, fade_ms=4000)
        
    def music_pause(self):
        pygame.mixer_music.pause()
        
    def music_resume(self):
        pygame.mixer_music.unpause()
        
    def update_volumes(self):
        pygame.mixer_music.set_volume(god.settings.music_vol)
        for sound in self.sounds.values():
            sound.update_volume(god.settings.fx_vol)
        
class SoundAsset:
    def __init__(self, pg_sounds, name, volume=1):
        self.pg_sounds: list[pygame.mixer.Sound] = pg_sounds
        for sound in self.pg_sounds:
            sound.set_volume(volume)
        self.volume = volume
        self.name = name
        
    def update_volume(self, volume):
        for sound in self.pg_sounds:
            sound.set_volume(self.volume*volume)
            
    def play(self):
        self.pg_sounds[0].play()
    
    def play_random(self):
        random.choice(self.pg_sounds).play()
        
    def stop(self):
        for sound in self.pg_sounds:
            sound.stop()
    
def single(name: str, volume=1):
    try:
        return SoundAsset([pygame.mixer.Sound(f"assets/sounds/{name}.wav")], name, volume)
    except FileNotFoundError:
        return SoundAsset([pygame.mixer.Sound(f"assets/sounds/{name}.mp3")], name, volume)

def folder(name: str, volume=1):
    return SoundAsset([pygame.mixer.Sound(f"assets/sounds/{name}/{fn}")
                        for fn in os.listdir(f"assets/sounds/{name}")], name, volume)        
