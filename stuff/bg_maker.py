import pygame
import random

pygame.init()
OW, OH = 1920, 1080
win = pygame.Window("Evergreen Defense Icon Maker", ((1920*2, 1080*2)))
clock = pygame.Clock()

STAR_COLORS = {
    n: (c[0]*255, c[1]*255, c[2]*255, c[3]*0.5*255) 
    for n, c in
    {"blue": (0, 0.3, 1, 0.7),
    "water": (0, 0.7, 1, 0.7),
    "yellow": (1, 1, 0, 0.7),
    "fluo": (1, 1, 0.3, 0.7),
    "purple": (1, 0, 1, 0.7),
    "orange": (1, 0.6, 0, 0.7),
    "red": (1, 0.1, 0, 0.7)}.items()
}

DUST1_START = pygame.Color(255,150,0,255)
DUST1_END = pygame.Color(255, 0, 255, 255)
DUST2_START = pygame.Color(255,50,0,255)
DUST2_END = pygame.Color(255, 20, 255, 255)

UNIT = 30

particle = pygame.image.load("assets/images/particles/particle.png")
particle.set_colorkey("black")

stars = {
    name: pygame.image.load(f"assets/images/stars/{name}.png")
    for name in STAR_COLORS.keys()
}
for v in stars.values():
    v.set_colorkey("black")

surf = pygame.Surface(win.size)
surf.fill("black")

for x in range(0, int(win.size[0]), UNIT):
    for y in range(0, int(win.size[0]), UNIT):
        if random.randint(0, 100) < 15:
            pos = x+random.randint(0, UNIT), y+random.randint(0, UNIT)
            size = random.randint(1, 3)
            col = (random.randint(200,255), random.randint(200, 255), random.randint(200, 255), 150)
            starbg = pygame.transform.scale(particle, (size*3, size*3))
            starbg.fill(col, special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(starbg, starbg.get_rect(center=pos))
            pygame.draw.circle(surf, col[:3], pos, int(size/2))
            
for i in range(12):
    pos = random.randint(0, win.size[0]), random.randint(0, win.size[1])
    if random.randint(0, 100) < 50:
        color = DUST1_START.lerp(DUST1_END, random.uniform(0.0, 1.0))
    else:
        color = DUST2_START.lerp(DUST2_END, random.uniform(0.0, 1.0))
    color.a = random.randint(70,120)
    size = random.randint(int(OW/2.5), int(OW/1.5))
    rect = pygame.Rect(0, 0, size, size).move_to(center=pos)
    dust = pygame.transform.scale(particle, (size, size))
    dust.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(dust, rect)
    surf.blit(dust, rect.move(win.size[0], 0))
    surf.blit(dust, rect.move(0, win.size[1]))
    surf.blit(dust, rect.move(-win.size[0], 0))
    surf.blit(dust, rect.move(0, -win.size[1]))
    surf.blit(dust, rect.move(win.size[0], win.size[1]))
    surf.blit(dust, rect.move(win.size[0], -win.size[1]))
    surf.blit(dust, rect.move(-win.size[0], -win.size[1]))
    surf.blit(dust, rect.move(-win.size[0], win.size[1]))
    
for i in range(4):
    pos = random.randint(0, win.size[0]), random.randint(0, win.size[1])
    name = random.choice(list(STAR_COLORS.keys()))
    col = STAR_COLORS[name]
    size = random.randint(200, 400)
    star = pygame.transform.scale(stars[name], (size, size))
    dust = pygame.transform.scale(particle, (int(size*2.5), int(size*2.5)))
    dust.fill(col, special_flags=pygame.BLEND_RGBA_MULT)
    starrect = pygame.Rect(0, 0, size, size).move_to(center=pos)
    rect = pygame.Rect(0, 0, size*2.5, size*2.5).move_to(center=pos)
    surf.blit(dust, rect)
    surf.blit(dust, rect.move(win.size[0], 0))
    surf.blit(dust, rect.move(0, win.size[1]))
    surf.blit(dust, rect.move(-win.size[0], 0))
    surf.blit(dust, rect.move(0, -win.size[1]))
    surf.blit(dust, rect.move(win.size[0], win.size[1]))
    surf.blit(dust, rect.move(-win.size[0], -win.size[1]))
    surf.blit(dust, rect.move(win.size[0], -win.size[1]))
    surf.blit(dust, rect.move(-win.size[0], win.size[1]))
    surf.blit(star, starrect)
    surf.blit(star, starrect.move(win.size[0], 0))
    surf.blit(star, starrect.move(0, win.size[1]))
    surf.blit(star, starrect.move(-win.size[0], 0))
    surf.blit(star, starrect.move(0, -win.size[1]))
    surf.blit(star, starrect.move(win.size[0], win.size[1]))
    surf.blit(star, starrect.move(-win.size[0], -win.size[1]))
    surf.blit(star, starrect.move(win.size[0], -win.size[1]))
    surf.blit(star, starrect.move(-win.size[0], win.size[1]))

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            exit()
        if e.type == pygame.KEYDOWN:
            pygame.image.save(surf, "stuff/EvergreenDefenseBGNew.png")
            print("saved")
            
    win.get_surface().blit(pygame.transform.scale(surf, (OW, OH)), (OW/2, OH/2))
    win.flip()
    clock.tick(60)
    