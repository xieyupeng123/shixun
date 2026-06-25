WIDTH = 1280
HEIGHT = 720
FPS = 120
TILESIZE = 64
HITBOX_OFFSET = {
    'player': -26,
    'object': -40,
    'grass': -10,
    'invisible': 0
}

# weapons
weapon_data = {
    'sword':  {'cooldown': 100, 'damage': 15},
    'lance':  {'cooldown': 400, 'damage': 30},
    'axe':    {'cooldown': 300, 'damage': 20},
    'rapier': {'cooldown': 50,  'damage': 8},
    'sai':    {'cooldown': 80,  'damage': 10},
}

# magic
magic_data = {
    'flame': {'strength': 10, 'cost': 20},
    'heal':  {'strength': 50, 'cost': 10},
}

# enemies
monster_data = {
    'squid': {'health': 50,  'exp': 100, 'damage': 15,
              'speed': 150, 'resistance': 3,
              'attack_radius': 80, 'notice_radius': 360},
    'boss':  {'health': 300, 'exp': 500, 'damage': 30,
              'speed': 80, 'resistance': 5,
              'attack_radius': 120, 'notice_radius': 500},
}

# boss phase thresholds
BOSS_PHASE_THRESHOLDS = [0.66, 0.33]  # % HP remaining

# colors
WATER_COLOR = '#71ddee'
