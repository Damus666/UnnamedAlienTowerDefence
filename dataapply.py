import json
import os

with open("stuff/treedatas.json", "r") as file:
    trees = json.load(file)
    
with open("stuff/enemydatas.json", "r") as file:
    enemies = json.load(file)

for tree in trees:
    if os.path.exists(f"assets/scriptables/trees/{tree['name']}.json"):
        with open(f"assets/scriptables/trees/{tree['name']}.json", "r") as file:
            tree_data = json.load(file)
        tree_data["grow_time"] = 1#tree["grow time"]
        tree_data["unlock_level"] = tree["level"]
        tree_data["attack_range"] = tree["range"]
        tree_data["attack_cooldown"] = tree["cooldown"]
        tree_data["price"] = tree["price"]
        en,enc = tree["energy,consume"].split(",")
        tree_data["energy"], tree_data["energy_price"] = float(en), float(enc)
        tree_data["place_xp"] = tree["xp"]
        if "proj" in tree_data:
            tree_data["proj"]["damage"] = tree["damage"]
            tree_data["proj"]["speed"] = tree["speed"]
        if "effect" in tree_data:
            tree_data["effect"]["ticks"] = tree["effect ticks"]
            if "damage" in tree_data["effect"]:
                ename = "damage"
            else:
                ename = "speed_mul"
            tree_data["effect"][ename] = tree["effect attr"]
        if "burst" in tree_data:
            num, time = tree["burst num, time"].split(",")
            num, time = int(num), float(time)
            tree_data["burst"]["amount"] = num
            tree_data["burst"]["cooldown"] = time
        if "split" in tree_data:
            dmg, speed, dist = tree["split dmg, speed, dist"].split(",")
            dmg, speed, dist = float(dmg), float(speed), float(dist)
            tree_data["split"]["damage"] = dmg
            tree_data["split"]["speed"] = speed
            tree_data["split"]["dist"] = dist
        if "area" in tree_data:
            dmg, rad, tm = tree["area dmg, rad, tm"].split(",")
            dmg, rad, tm = float(dmg), float(rad), float(tm)
            tree_data["area"]["damage"] = dmg
            tree_data["area"]["radius"] = rad
            tree_data["area"]["grow_time"] = tm
        if "beam" in tree_data:
            dmg, ticks = tree["beam dmg, ticks"].split(",")
            dmg, ticks = float(dmg), int(ticks)
            tree_data["beam"]["damage"] = dmg
            tree_data["beam"]["ticks"] = ticks
        with open(f"assets/scriptables/trees/{tree['name']}.json", "w") as file:
            json.dump(tree_data, file, indent="\t")

for enemy in enemies:
    if os.path.exists(f"assets/scriptables/enemies/{enemy['color']}_bot.json"):
        with open(f"assets/scriptables/enemies/{enemy['color']}_bot.json", "r") as file:
            enemy_data = json.load(file)
        enemy_data["health"] = enemy["health"]
        enemy_data["speed"] = enemy["speed"]
        enemy_data["reward_mul"] = enemy["reward mul"]
        enemy_data["xp"] = enemy["xp"]
        if "buff" in enemy_data:
            enemy_data["buff"] = enemy["buff"]
        with open(f"assets/scriptables/enemies/{enemy['color']}_bot.json", "w") as file:
            json.dump(enemy_data, file, indent="\t")
            