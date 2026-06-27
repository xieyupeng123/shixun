"""
Game constants — entity codes, layer identifiers, and sprite types.
Centralizes values that were previously scattered as inline literals.
"""


# ── Entity CSV codes (used in map_Entities.csv) ──────────────────────────
ENTITY_PLAYER_SPAWN = '394'
ENTITY_BOSS_SPAWN = '392'
ENTITY_BAMBOO = '390'
ENTITY_SPIRIT = '391'
ENTITY_SQUID = '393'

# Mapping from CSV code to monster name
ENTITY_MONSTER_MAP = {
    ENTITY_BAMBOO: 'bamboo',
    ENTITY_SPIRIT: 'spirit',
    ENTITY_SQUID: 'squid',
}

# ── Sprite types ─────────────────────────────────────────────────────────
SPRITE_GRASS = 'grass'
SPRITE_OBJECT = 'object'
SPRITE_INVISIBLE = 'invisible'

# ── Map layer names ──────────────────────────────────────────────────────
LAYER_BOUNDARY = 'boundary'
LAYER_GRASS = 'grass'
LAYER_OBJECT = 'object'
LAYER_ENTITIES = 'entities'
