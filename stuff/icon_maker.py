import pygame

pygame.init()
win = pygame.Window("Evergreen Defense Icon Maker", (630, 500))
clock = pygame.Clock()

portal = pygame.image.load("assets/images/enemies/boss_bot.png")
portal.set_colorkey((0, 0, 0, 1))
rock = pygame.image.load("assets/images/tiles/rockblock.png")

old_w = portal.get_width()
portal = pygame.transform.scale(portal, (500, 500))
ratio = portal.get_width()/old_w
rock = pygame.transform.scale_by(rock, ratio)

center = pygame.Vector2(315, 253)

surf = pygame.Surface(win.size)

surf.fill("black")
    
for x in range(0, 10*rock.get_width(), rock.get_width()):
    for y in range(0, 8*rock.get_width(), rock.get_width()):
        surf.blit(rock, (x, y))

surf.blit(portal, pygame.Rect((0, 0), portal.get_size()).move_to(center=center))

for px in range(surf.get_width()):
    for py in range(surf.get_height()):
        color = surf.get_at((px, py))
        direction = (px-center.x, py-center.y)-pygame.Vector2(0, 0)
        dist2 = direction.dot(direction)
        range2 = 450*450
        attenuation = max(1.0 - dist2 / range2, 0.0)
        expr = attenuation*2.5
        prev = color.r
        color.r = pygame.math.clamp(int(((color.r/255)*(expr))*255), 0, 255)
        if color.r < prev:
            color.r = prev
        surf.set_at((px, py), color)

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            exit()
        if e.type == pygame.KEYDOWN:
            pygame.image.save(surf, "stuff/EvergreenDefenseIconNew.png")
            print("saved")
            
    win.get_surface().blit(surf, (0, 0))
    win.flip()
    clock.tick(60)