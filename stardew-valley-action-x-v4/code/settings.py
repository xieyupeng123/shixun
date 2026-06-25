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

# weapons (multiple types)
weapon_data = {
    'sword':  {'cooldown': 100, 'damage': 15},
    'lance':  {'cooldown': 400, 'damage': 30},
    'axe':    {'cooldown': 300, 'damage': 20},
    'rapier': {'cooldown': 50,  'damage': 8},
    'sai':    {'cooldown': 80,  'damage': 10},
}

# enemy
monster_data = {
    'slime': {
        'health': 50, 'exp': 40, 'damage': 8,
        'speed': 100, 'resistance': 2,
        'attack_radius': 60, 'notice_radius': 300,
    },
}

# colors
WATER_COLOR = '#71ddee'
