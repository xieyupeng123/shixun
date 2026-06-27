from support import get_path

# game setup
WIDTH = 1280
HEIGHT = 720
FPS = 60
TILESIZE = 64
HITBOX_OFFSET = {
    'player': -26,
    'object': -40,
    'grass': -10,
    'invisible': 0
}

# ui
BAR_HEIGHT = 20
HEALTH_BAR_WIDTH = 200
ENERGY_BAR_WIDTH = 140
ITEM_BOX_SIZE = 80
UI_FONT = get_path('../font/joystix.ttf')
UI_FONT_SIZE = 18

# general colors
WATER_COLOR = '#71ddee'
UI_BG_COLOR = '#222222'
UI_BORDER_COLOR = '#111111'
TEXT_COLOR = '#EEEEEE'

# ui colors
HEALTH_COLOR = 'red'
ENERGY_COLOR = 'blue'
UI_BORDER_COLOR_ACTIVE = 'gold'

# upgrade menu
TEXT_COLOR_SELECTED = '#111111'
BAR_COLOR = '#EEEEEE'
BAR_COLOR_SELECTED = '#111111'
UPGRADE_BG_COLOR_SELECTED = '#EEEEEE'

# weapons
sword_path = get_path('../graphics/weapons/sword/full.png')
lance_path = get_path('../graphics/weapons/lance/full.png')
axe_path = get_path('../graphics/weapons/axe/full.png')
rapier_path = get_path('../graphics/weapons/rapier/full.png')
sai_path = get_path('../graphics/weapons/sai/full.png')

weapon_data = {
    'sword': {'cooldown': 100, 'damage': 15, 'graphic': sword_path},
    'lance': {'cooldown': 400, 'damage': 30, 'graphic': lance_path},
    'axe': {'cooldown': 300, 'damage': 20, 'graphic': axe_path},
    'rapier': {'cooldown': 50, 'damage': 8, 'graphic': rapier_path},
    'sai': {'cooldown': 80, 'damage': 10, 'graphic': sai_path}
}

# magic
flame_path = get_path('../graphics/particles/flame/fire.png')
heal_path = get_path('../graphics/particles/heal/heal.png')

flame_sound_path = get_path('../audio/flame.wav')
heal_sound_path = get_path('../audio/heal.wav')

magic_data = {
    'flame': {'strength': 10, 'cost': 20, 'graphic': flame_path, 'spell_sound': flame_sound_path},
    'heal': {'strength': 50, 'cost': 10, 'graphic': heal_path, 'spell_sound': heal_sound_path},
}

# enemy
slash_sound_path = get_path('../audio/attack/slash.wav')
claw_sound_path = get_path('../audio/attack/claw.wav')
fireball_sound_path = get_path('../audio/attack/fireball.wav')

monster_data = {
    'squid': {'health': 50, 'exp': 100, 'damage': 15, 'attack_type': 'slash', 'attack_sound': slash_sound_path, 'speed': 150, 'resistance': 3, 'attack_radius': 80, 'notice_radius': 360},
    'raccoon': {'health': 300, 'exp': 500, 'damage': 40, 'attack_type': 'claw',  'attack_sound': claw_sound_path, 'speed': 100, 'resistance': 3, 'attack_radius': 120, 'notice_radius': 400},
    'spirit': {'health': 40, 'exp': 110, 'damage': 8, 'attack_type': 'thunder', 'attack_sound': fireball_sound_path, 'speed': 200, 'resistance': 3, 'attack_radius': 60, 'notice_radius': 350},
    'bamboo': {'health': 35, 'exp': 120, 'damage': 5, 'attack_type': 'leaf_attack', 'attack_sound': slash_sound_path, 'speed': 150, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 300}}

# invincible state
INVINCIBLE_SPEED_MULT = 2       # movement speed multiplier
INVINCIBLE_ATTACK_MULT = 2      # attack damage multiplier

# player base stats and costs (single source of truth for upgrades)
PLAYER_BASE_STATS = {'health': 200, 'energy': 100, 'attack': 15, 'magic': 5, 'speed': 300}
PLAYER_BASE_COSTS = {'health': 100, 'energy': 100, 'attack': 100, 'magic': 100, 'speed': 100}

# boss phase system
BOSS_PHASE_DATA = {
    1: {'color': None, 'stat_mult': 1.0},              # normal
    2: {'color': (255, 120, 120), 'stat_mult': 2.0},   # light red + double stats
    3: {'color': (180, 80, 220), 'stat_mult': 4.0},    # purple + quadruple stats
}
