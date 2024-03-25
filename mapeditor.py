import pygame
import sys
import json

pygame.init()
screen = pygame.display.set_mode((500, 500))
clock = pygame.Clock()

out_dir = "assets/maps/"
map_idx = 0
font = pygame.Font(None, 25)
px_scale = 10
marginright = 200
pencil_size = 3
extra_height = 4

def draw_text(text, h):
    surf = font.render(str(text), True, "white")
    rect = surf.get_rect(topright=(screen.get_width()-5, h))
    screen.blit(surf, rect)
    return rect.h
    
def make_px(pos):
    return (pos[0]+next_width//2, pos[1]+next_height//2)
    
def load():
    with open(f"{out_dir}{map_idx}.json", "r") as file:
        data = json.load(file)
    for pos, block in data["floor"].items():
        x, y = pos.split(";")
        x, y = eval(x), eval(y)
        pixels[make_px((x, y))] = block
    if data["spawn"] is not None:
        pixels[make_px(data["spawn"])] = 8
    for pos in data["pos"]:
        pixels[make_px(pos)] = 9
    
def save():
    data = {
        "floor": {},
        "height": {},
        "spawn": None,
        "pos": [],
        "collision": [],
        "oxygen": []
    }
    for pixel, block in pixels.items():
        pos = (pixel[0]-next_width//2, pixel[1]-next_height//2)
        if block == 9:
            data["pos"].append(pos)
            data["floor"][f"{pos[0]};{pos[1]}"] = 1
            bottom = (pixel[0], pixel[1]+1)
            if bottom not in pixels:
                for i in range(1, extra_height+1):
                    data["height"][f"{pos[0]};{pos[1]+i}"] = 1
                    data["collision"].append((pos[0], pos[1]+i))
        elif block == 8:
            data["spawn"] = pos
            data["floor"][f"{pos[0]};{pos[1]}"] = 1
        elif block == 10:
            data["oxygen"].append(pos)
            data["floor"][f"{pos[0]};{pos[1]}"] = 2
            bottom = (pixel[0], pixel[1]+1)
            if bottom not in pixels:
                for i in range(1, extra_height+1):
                    data["height"][f"{pos[0]};{pos[1]+i}"] = 2
                    data["collision"].append((pos[0], pos[1]+i))
        else:
            data["floor"][f"{pos[0]};{pos[1]}"] = block
            up = (pixel[0], pixel[1]-1)
            left = (pixel[0]-1, pixel[1])
            right = (pixel[0]+1, pixel[1])
            if up not in pixels:
                data["collision"].append((pos[0], pos[1]-1))
            if left not in pixels:
                data["collision"].append((pos[0]-1, pos[1]))
            if right not in pixels:
                data["collision"].append((pos[0]+1, pos[1]-1))
            bottom = (pixel[0], pixel[1]+1)
            if bottom not in pixels:
                for i in range(1, extra_height+1):
                    data["height"][f"{pos[0]};{pos[1]+i}"] = block
                    data["collision"].append((pos[0], pos[1]+i))
    with open(f"{out_dir}{map_idx}.json", "w") as file:
        json.dump(data, file)
    
next_width = 100
next_height = 100

width_txt = ""
height_txt = ""

in_width = False
in_height = False

selected = 2
colors = {
    1: "dark gray",
    2: "purple",
    9: "blue",
    8: "red",
    3: "light blue",
    4: "orange",
    5: "dark blue",
    6: "green",
    10: "magenta"
}
names = {
    0: "Erase",
    1: "Rock",
    2: "Grass",
    9: "Pos",
    8: "Spawn",
    3: "Iron",
    4: "Copper",
    5: "Titanium",
    6: "Tioplasm",
    10: "Oxygen"
    
}

def resize():
    global width_txt, height_txt, screen
    screen = pygame.display.set_mode((next_width*px_scale+marginright, next_height*px_scale))
    width_txt = ""
    height_txt = ""

resize()
    
pixels = {}

while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.unicode.isdecimal():
                if in_width:
                    width_txt += event.unicode
                elif in_height:
                    height_txt += event.unicode
                else:
                    num = int(event.unicode)
                    if keys[pygame.K_m]:
                        map_idx = num
                    elif keys[pygame.K_p]:
                        pencil_size = num
                    elif keys[pygame.K_b]:
                        selected = num
                    elif keys[pygame.K_n]:
                        selected = num+10
            if event.key == pygame.K_l:
                load()
            elif event.key == pygame.K_s:
                save()
            elif event.key == pygame.K_w:
                in_width = True
                width_txt = ""
                height_txt = ""
            elif event.key == pygame.K_h:
                in_height = True
                in_width = False
                next_width = int(width_txt)
            elif event.key == pygame.K_RETURN:
                in_height = False
                next_height = int(height_txt)
                resize()

    screen.fill("black")
    
    i = 5
    i += draw_text(f"Map ID: {map_idx}", i)
    if width_txt != "":
        i += 5
        i += draw_text(f"Next W: {width_txt}", i)
    if height_txt != "":
        i += 5
        i += draw_text(f"Next H: {height_txt}", i)
    if not in_width and not in_height:
        i += 5
        i += draw_text(f"Map W: {next_width}", i)
        i += 5
        i += draw_text(f"Map H: {next_height}", i)
    i += 5
    i += draw_text(f"Pencil: {pencil_size}", i)
    i += 5
    i += draw_text(f"Block: {names[selected]}", i)
    
    if pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:
        prev = selected
        if pygame.mouse.get_pressed()[2]:
            selected = 0
        mouse = pygame.mouse.get_pos()
        px = (mouse[0]//px_scale, mouse[1]//px_scale)
        pxs = [px]
        if selected not in [9, 8, 10]:
            if pencil_size != 1:
                for i in range(-pencil_size//2, pencil_size//2):
                    for j in range(-pencil_size//2, pencil_size//2):
                        if i != 0 or j!= 0:
                            pxs.append((px[0]+i, px[1]+j))
                    
        for p in pxs:
            if selected != 0:
                if p in pixels and selected in [1, 2] and pixels[p] in [9, 8]:
                    continue
                if p not in pixels and selected not in [1, 2]:
                    continue
                if p[0] <= next_width:
                    pixels[p] = selected
            else:
                if p in pixels:
                    del pixels[p]
        if pygame.mouse.get_pressed()[2]:
            selected = prev
            
    for pixel, block in pixels.items():
        pygame.draw.rect(screen, colors[block], (pixel[0]*px_scale, pixel[1]*px_scale, px_scale, px_scale))
        
    pygame.draw.line(screen, "red", ((next_width+1)*px_scale+1, 0), ((next_width+1)*px_scale+1, screen.get_height()))
    
    clock.tick(0)
    pygame.display.flip()
    