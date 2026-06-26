WIDTH = 1280
HEIGHT = 720
FPS = 120
TILESIZE = 64
HITBOX_OFFSET = {
    'player': -26, 'object': -40, 'grass': -10, 'invisible': 0
}

weapon_data = {
    'sword':  {'cooldown': 100, 'damage': 15,
               'graphic': '../graphics/weapons/sword/full.png'},
    'lance':  {'cooldown': 400, 'damage': 30,
               'graphic': '../graphics/weapons/lance/full.png'},
    'axe':    {'cooldown': 300, 'damage': 20,
               'graphic': '../graphics/weapons/axe/full.png'},
    'rapier': {'cooldown': 50,  'damage': 8,
               'graphic': '../graphics/weapons/rapier/full.png'},
    'sai':    {'cooldown': 80,  'damage': 10,
               'graphic': '../graphics/weapons/sai/full.png'},
}

magic_data = {
    'flame': {'strength': 10, 'cost': 20,
              'graphic': '../graphics/particles/flame/fire.png'},
    'heal':  {'strength': 50, 'cost': 10,
              'graphic': '../graphics/particles/heal/heal.png'},
}

monster_data = {
    'squid':  {'health': 50,  'exp': 100, 'damage': 15,
               'speed': 150, 'resistance': 3,
               'attack_radius': 80, 'notice_radius': 360},
    'bamboo': {'health': 35,  'exp': 120, 'damage': 5,
               'speed': 150, 'resistance': 3,
               'attack_radius': 50, 'notice_radius': 300},
    'spirit': {'health': 40,  'exp': 110, 'damage': 8,
               'speed': 200, 'resistance': 3,
               'attack_radius': 60, 'notice_radius': 350},
    'boss':   {'health': 300, 'exp': 500, 'damage': 30,
               'speed': 80, 'resistance': 5,
               'attack_radius': 120, 'notice_radius': 500},
}

BOSS_PHASE_THRESHOLDS = [0.66, 0.33]
BOSS_PHASE_COLORS = [
    (255, 255, 255), (255, 120, 120), (180, 80, 220)]
BOSS_PHASE_NAMES = ['Normal', 'Enraged', 'Final']

INVINCIBLE_SPEED_MULT = 2.0
INVINCIBLE_ATTACK_MULT = 2.0

WATER_COLOR = '#71ddee'
