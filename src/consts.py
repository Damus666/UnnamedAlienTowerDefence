import pygame
import sys
from .scriptables import TreeData, EnemyData, MapData, BuildingData, ENERGY_SOURCE, ENERGY_DISTRIBUTOR, MINER, BOT # noqa: F401
pygame.init()

# window
WIDTH, HEIGHT = pygame.display.get_desktop_sizes()[0]
#WIDTH, HEIGHT = 1200, 800
TITLE = "Evergreen Defense"
FPS = 0
PREF_LANGUAGE, DEFAULT_LANGUAGE = pygame.system.get_pref_locales()[0]["language"], "en"
ORG, APP = "PixmoGames", "EvergreenDefense"

# camera
PROJ_SIZE = 10
ZOOM_MUL = 0.1
ZOOM_MIN = 0.3
ZOOM_MAX = 4.4

# shader
LIT_SHADER = "lit"
UNLIT_SHADER = "unlit"
UI_SHADER = "ui"
REPLACE_SHADER = "replace"

# shader uniforms
SHADER_UNIFORMS = "2f 4f 2f 1f", "vPos", "vCol", "vUV", "vTexID"
TEXTURES_UNIFORM = "textures"
MAX_SAMPLERS = 3
MAX_LIGHTS = 100

WORLD_ATLAS = 0
UI_ATLAS = 1
FONT_ATLAS = 2

# sizes
OBJ_SIZE = 1
TREE_SIZE = OBJ_SIZE*2
OXYGEN_SIZE = TREE_SIZE
SPAWNER_SIZE = TREE_SIZE*2+1
BASE_SIZE = 8
TREE_HITBOX_SIZE = ((OBJ_SIZE*2)/8, (OBJ_SIZE*2)/8)
HALF_COLLIDER_H = OBJ_SIZE/1.5

# ui
S = 0.05
MAIN_FONT = "main"

OUTLINE_SIZES = {
    "t": 1,
    "s": 2,
    #"o": 3,
    "b": 6,
    "v": 8,
    "u": 10,
    "i": 15,
    "m": 20
}
CIRCLE_RADIUS = 100
FONT_SCALE = (0.02/6)*(0.6/1.5)
FPS_OPTIONS = [30, 60, 90, 120, 244, 360, 666, 0]

MOUSE_CONVERSION = {
    pygame.BUTTON_LEFT: "left-button",
    pygame.BUTTON_RIGHT: "right-button",
    pygame.BUTTON_MIDDLE: "middle-button"
}

PRB_H, PRB_C = 0.8, 0.4
WORLD_BAR_XMUL, WORLD_BAR_H, WORLD_BAR_C = 1.2, 0.15, 0.04
TL_BAR_W, TL_BAR_O = 3.5, 3.5*2
LEVEL_CIRCLE_TL, LEVEL_CIRCLE_SIZE = (S, PRB_H/2+S), (1, 1)
MONEY_ICON_W = 0.72

TITLE_SIZE = 3.2
DAMAGE_OVERLAY = "damageoverlay"
SHOP_CARD_W, SHOP_CARD_C = 3, 0.5
CARD_S, UI_S = 0.15, 0.14
BBTN_SIZE, BTN_C = (4, 1.2), 0.16
MBTN_SIZE = (3, 1)
SBTN_SIZE = (1.5, 0.8)
BTN_TEXT, LABEL_SIZE = 1.2, 1.3

OVERLAYBTN_SIZE = (1, 1)
OVERLAYINNER_SIZE = (0.74, 0.74)

# colors
DUST1_START = pygame.Color(255,150,0,255)
DUST1_END = pygame.Color(255, 0, 255, 255)
DUST2_START = pygame.Color(255,50,0,255)
DUST2_END = pygame.Color(255, 20, 255, 255)

TREE_OK_COL = (0, 0.7, 0.8, 0.6)
TREE_BAD_COL = (1, 0, 0, 0.6)
BUILDING_OK_COL = (0, 0.9, 0.3, 0.6)
BUILDING_BAD_COL = (1, 0, 0, 0.6)
PREVIW_RANGE_COL = (0, 0.7, 0.8, 0.4)
PREVIW_ENERGY_COL = (0, 1, 0.3, 0.4)
DESTROY_COLOR = (1, 0, 0, 0.6)

ENEMY_DAMAGE_COL = (1, 0, 0, 1)
PORTAL_COL = (1.1, 1, 1, 0.6)
WHITE = (1, 1, 1, 1)
BLACK = (0, 0, 0, 1)

BAR_OUTLINE = (1, 1, 1, 0.4)
DARK_OUTLINE = (0, 0, 0, 1)
HEALTH_BAR_FILL, HEALTH_BAR_BG = (1, 0, 0, 0.3), (0.4, 0, 0, 0.3)
COOLDOWN_BAR_FILL, COOLDOWN_BAR_BG = (1, 1, 1, 0.4), (0.7, 0.7, 0.7, 0.4)
XP_BAR_FILL, XP_BAR_BG = (0, 0.6, 1, 0.4), (0, 0.2, 0.5, 0.4)
ENERGY_BAR_FILL, ENERGY_BAR_BG = (1, 0.9, 0, 0.6), (0.7, 0.6, 0, 0.6)

MONEY_COL = (1, 0.8, 0, 1)
LOCKED_IMG_COL = (1, 1, 1, 0.4)
UNHOVER_OUTLINE, HOVER_OUTLINE = (0.6, 0.6, 0.6, 0.6), (1, 1, 1, 1)
CARD_BG = (0, 0, 0, 0.6)
BTN_BG = (0, 0, 0, 0.6)

STAR_COLORS = {
    "blue": (0, 0.3, 1, 0.7),
    "water": (0, 0.7, 1, 0.7),
    "yellow": (1, 1, 0, 0.7),
    "fluo": (1, 1, 0.3, 0.7),
    "purple": (1, 0, 1, 0.7),
    "orange": (1, 0.6, 0, 0.7),
    "red": (1, 0.1, 0, 0.7)
}

# player
PLAYER_LIGHT_RANGE = 16
PLAYER_LIGHT_COL = (1,1,1)
PLAYER_LIGHT_INTENSITY = 1

PLAYER_SPEED = 12
PLAYER_IDLE_SPEED = 4
PLAYER_RUN_SPEED = 10

PLAYER_MAX_ENERGY = 100
NEXT_LEVEL_START_XP = 500
NEXT_LEVEL_XP_MUL = 1.5
PLAYER_START_MONEY = 500

P_BLOCK_I, P_DESTROY_I, P_PREVIEW_I, P_RANGEPREV_I = 0, 1, 3, 2
PLAYER_INVENTORY = ["bot", "energy_distributor", "energy_source", "miner"]

# noise
PLANT_OCTAVES = 2
PLANT_SCALE = 0.022

ROVE_OCTAVES = 3
ROVE_SCALE = 0.08

# world data
PLANT_CHUNK_DIST = 16
TREE_CHUNK_DIST = 8
MINER_CHUNK_DIST = 4
TREE_UI_DIST = 15
ENEMY_UI_DIST = 20
PLANT_OFFSET = 0.35
MAP_PADDING = 80

LILSTAR_CHANCE = 15
DUST_CHANCE_RANGE = 1300
STAR_CHANCE_RANGE = 3500

MAX_CAN_BE_ABOVE = 20
ABOVE_MAX_DIST = 6

WAVE_XP = 100
WAVE_COOLDOWN = 45
ENERGY_DISTANCE = 8
PORTAL_ROT_SPEED = 12
BOT_SPEED = 5
DAMAGE_OVERLAY_DURATION = 1.2
EVENT_UI_DURATION = 2

ATTACK_SINGLE, ATTACK_BURST = "single", "burst"
ENEMY_DAMAGE_COOLDOWN = 0.5
TICK = 1
CURE_AMOUNT = 2

EFFECT_PARTICLE_SIZE = 0.5
EFFECT_PARTICLE_SPEED = 4
EFFECT_PARTICLE_DIST = 1.5

# tiles
ROCK_TILE = "rockblock"
GRASS_TILE = "grasssideblock"
GRASS_SIDE_TILE = "grassblock"
ROCK_SIDE_TILE = "rockblock"
HALF_GRASS_TILE = "halfgrassblock"
FLIP_GRASS_TILE = "grasstopblock"

IRON_TILE = "ironoreblock"
COPPER_TILE = "copperoreblock"
TITANIUM_TILE = "titaniumoreblock"
TIOPLASM_TILE = "tioplasmoreblock"

IRON, COPPER, TITANIUM, TIOPLASM = "iron", "copper", "titanium", "tioplasm"
TILES_ORES = {
    IRON_TILE: IRON,
    COPPER_TILE: COPPER,
    TITANIUM_TILE: TITANIUM,
    TIOPLASM_TILE: TIOPLASM
}

ORES_DATA = {
    # cooldown, stack_size, energy
    IRON: [0.7, 30, 3],
    COPPER: [1, 25, 5],
    TITANIUM: [1.2, 18, 8],
    TIOPLASM: [2.3, 12, 15]
}

ROCKY_TILES = [ROCK_TILE, IRON_TILE, COPPER_TILE, TITANIUM_TILE, TIOPLASM_TILE]

GRASS_PLANT_TILE = "grass"
SPIRAL_TILE = "spiral"
FLOWERS_TILE = "flowers"
CACTUS_TILE = "cactus"
SPORES_TILE = "spores"
ROVE_TILE = "rove"

SPAWNER_TILE = "enemyportal"
PORTALFRAME_TILE = "portalframe"
BASE_TILE = "playerbasehd"
OXYGEN_TILE = "oxygen"
MINER_OFF = "mineroff"
ENERGY_TILES = ["energydist", "energysource"]

TILES_SIDE = {
    GRASS_TILE: GRASS_SIDE_TILE,
    ROCK_TILE: ROCK_SIDE_TILE
}

# light
SPAWNER_LIGHT_DATA = ([1, 0, 0], 12, 1.1)
BASE_LIGHT_DATA = ([0, 0.7, 1], 12, 1.1)

CHUNK_LIGHT_DATA = {
    GRASS_PLANT_TILE: ((1, 0, 1), 9, 0.5),
    SPIRAL_TILE: ((1, 0, 0), 8, 0.36),
    CACTUS_TILE: ((0.3, 1, 0), 7.5, 0.42),
    FLOWERS_TILE: ((0.3, 0.5, 1), 8, 0.42),
    ROVE_TILE: ([1, 0.8, 0.5], 7, 0.7)
}

# tools
NOTOOL_IDX = -1
PICAXE_IDX = 0
SICKLE_IDX = 1

# enemy buffs
BUFF_HEAL_AMOUNT, BUFF_HEAL_COOLDOWN = 20, 2
BUFF_ARMOR_HITS = 5
BUFF_MAX_SPEED = 3

# map load
LOAD_ROCK = 1
LOAD_GRASS = 2
LOAD_IRON = 3
LOAD_COPPER = 4
LOAD_TITANIUM = 5
LOAD_TIOPLASM = 6

LOAD_ROCKY = [LOAD_ROCK, LOAD_IRON, LOAD_COPPER, LOAD_TIOPLASM, LOAD_TITANIUM]

LOAD_NAMES = {
    LOAD_ROCK: ROCK_TILE,
    LOAD_GRASS: GRASS_TILE,
    LOAD_IRON: IRON_TILE,
    LOAD_COPPER: COPPER_TILE,
    LOAD_TITANIUM: TITANIUM_TILE,
    LOAD_TIOPLASM: TIOPLASM_TILE
}

# menu
PATH_SIZE = 4
PATH_OFFSET = 1
MENU_ENEMY_SPEED = 3
MENU_ENEMY_SIZE = (2, 2)
QUIT_SPACE_SIZES = (7, 4)
