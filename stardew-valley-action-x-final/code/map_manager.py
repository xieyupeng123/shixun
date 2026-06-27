"""
Map loading and world geometry construction.
Extracted from level.py to keep map concerns separate from gameplay logic.
"""
import pygame
import os
from settings import TILESIZE
from tile import Tile
from player import Player
from enemy import Enemy
from support import get_path, import_csv_layout, import_folder
from random import choice
from constants import (
    ENTITY_PLAYER_SPAWN, ENTITY_BOSS_SPAWN,
    ENTITY_MONSTER_MAP,
    LAYER_BOUNDARY, LAYER_GRASS, LAYER_OBJECT, LAYER_ENTITIES,
    SPRITE_GRASS, SPRITE_OBJECT, SPRITE_INVISIBLE,
)
from pathfinding_utils import build_grid, pos_to_grid, grid_to_pos

class MapManager:
    """Handles map CSV loading, tile placement, water detection,
    pathfinding grid construction, and entity spawning."""

    # Cached water obstacle positions (reset when map changes)
    _water_tiles_cache = None
    _water_tiles_map_id = None

    def __init__(self, level, map_id, loaded_data=None):
        self.level = level
        self.map_id = map_id
        self.loaded_data = loaded_data

    def load(self):
        """Load and populate the entire map into the Level's sprite groups."""
        level = self.level
        map_id = self.map_id
        loaded_data = self.loaded_data

        def map_file(layer):
            return f"../data/map/map_{map_id}_{layer}.csv"

        def file_or_default(path, default):
            return path if os.path.exists(path) else default

        layouts = {
            LAYER_BOUNDARY: import_csv_layout(file_or_default(map_file('FloorBlocks'), '../data/map/map_FloorBlocks.csv')),
            LAYER_GRASS: import_csv_layout(file_or_default(map_file('Grass'), '../data/map/map_Grass.csv')),
            LAYER_OBJECT: import_csv_layout(file_or_default(map_file('Objects'), '../data/map/map_Objects.csv')),
            LAYER_ENTITIES: import_csv_layout(file_or_default(map_file('Entities'), '../data/map/map_Entities.csv')),
        }

        if level._player_spawn_pos is None:
            map_width = len(layouts[LAYER_BOUNDARY][0]) * TILESIZE
            map_height = len(layouts[LAYER_BOUNDARY]) * TILESIZE
            level._player_spawn_pos = (map_width // 2, map_height // 2)

        graphics = {
            LAYER_GRASS: import_folder('../graphics/grass'),
            LAYER_OBJECT: import_folder('../graphics/objects'),
        }

        level.pathfinding_grid = None

        # ---- Layer 1: boundary, grass, objects ----
        for style, layout in layouts.items():
            for row_idx, row in enumerate(layout):
                for col_idx, col in enumerate(row):
                    if col == '-1':
                        continue
                    x = col_idx * TILESIZE
                    y = row_idx * TILESIZE

                    if style == LAYER_BOUNDARY:
                        Tile((x, y), [level.obstacle_sprites], SPRITE_INVISIBLE)

                    elif style == LAYER_GRASS:
                        destroyed = False
                        if loaded_data and 'destroyed_grass' in loaded_data:
                            for g in loaded_data['destroyed_grass']:
                                if g['x'] == x and g['y'] == y:
                                    destroyed = True
                                    break
                        if not destroyed:
                            img = choice(graphics[LAYER_GRASS])
                            Tile((x, y),
                                 [level.visible_sprites, level.obstacle_sprites, level.combat.attackable_sprites],
                                 SPRITE_GRASS, img)

                    elif style == LAYER_OBJECT:
                        surf = graphics[LAYER_OBJECT][int(col)]
                        Tile((x, y), [level.visible_sprites, level.obstacle_sprites],
                             SPRITE_OBJECT, surf)

        # ---- Pathfinding grid ----
        map_cols = len(layouts[LAYER_BOUNDARY][0]) if layouts[LAYER_BOUNDARY] else 0
        map_rows = len(layouts[LAYER_BOUNDARY])
        map_pixel_w = map_cols * TILESIZE
        map_pixel_h = map_rows * TILESIZE

        self._mark_water_tiles(map_cols, map_rows)
        level.pathfinding_grid = build_grid(map_pixel_w, map_pixel_h, TILESIZE, level.obstacle_sprites)

        # ---- Layer 2: entities (player, boss, enemies) ----
        entities_layout = layouts[LAYER_ENTITIES]
        for row_idx, row in enumerate(entities_layout):
            for col_idx, col in enumerate(row):
                if col == '-1':
                    continue
                x = col_idx * TILESIZE
                y = row_idx * TILESIZE

                if col == ENTITY_PLAYER_SPAWN:
                    if level.player is None:
                        spawn_pos = (x, y)
                        if level._player_spawn_pos is not None:
                            spawn_pos = level._player_spawn_pos
                        level.player = Player(
                            spawn_pos,
                            [level.visible_sprites],
                            level.obstacle_sprites,
                            level.create_attack,
                            level.destroy_attack,
                            level.create_magic)
                        if loaded_data and 'player' in loaded_data:
                            level.player.from_dict(loaded_data['player'])
                    else:
                        if level._player_spawn_pos is not None:
                            level.player.pos.x, level.player.pos.y = level._player_spawn_pos
                            level.player.rect.center = level._player_spawn_pos
                            level.player.hitbox.center = level._player_spawn_pos
                        level.player.obstacle_sprites = level.obstacle_sprites
                        level.player.create_attack = level.create_attack
                        level.player.destroy_attack = level.destroy_attack
                        level.player.create_magic = level.create_magic
                        level.visible_sprites.add(level.player)
                        self._ensure_safe_spawn()

                elif col == ENTITY_BOSS_SPAWN:
                    level.boss._boss_spawn_pos = (x, y)
                    level.boss.spawn_boss(phase=1)

                else:  # Regular enemies
                    defeated = False
                    if loaded_data and 'defeated_enemies' in loaded_data:
                        for e in loaded_data['defeated_enemies']:
                            if e['x'] == x and e['y'] == y:
                                defeated = True
                                break
                    if defeated:
                        continue
                    if col.startswith('9'):
                        continue
                    monster_name = ENTITY_MONSTER_MAP.get(col, 'squid')  # default to squid
                    Enemy(
                        monster_name, (x, y),
                        [level.visible_sprites, level.combat.attackable_sprites],
                        level.obstacle_sprites,
                        level.combat.damage_player,
                        level.trigger_death_particles,
                        level.add_exp,
                        lambda enemy_pos, player_pos, exp_amount=0, level=level:
                            level.trigger_exp_particles(enemy_pos, player_pos, exp_amount),
                        pathfinding_grid=level.pathfinding_grid,
                        tile_size=TILESIZE)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _mark_water_tiles(self, map_cols, map_rows):
        """Mark blue water tiles + border perimeter as obstacles. Cached per map_id."""
        level = self.level
        # Invalidate cache if map changed
        if MapManager._water_tiles_map_id != self.map_id:
            MapManager._water_tiles_cache = None
            MapManager._water_tiles_map_id = self.map_id

        if MapManager._water_tiles_cache is not None:
            for wx, wy in MapManager._water_tiles_cache:
                Tile((wx, wy), [level.obstacle_sprites], SPRITE_INVISIBLE)
            return

        floor_path = get_path('../graphics/tilemap/ground.png')
        MapManager._water_tiles_cache = []
        border = 2

        # Perimeter border (outer 2 tiles always blocked)
        for row in range(map_rows):
            for col in range(map_cols):
                if row < border or row >= map_rows - border or col < border or col >= map_cols - border:
                    MapManager._water_tiles_cache.append((col * TILESIZE, row * TILESIZE))
                    Tile((col * TILESIZE, row * TILESIZE), [level.obstacle_sprites], SPRITE_INVISIBLE)

        # Water pixel detection from ground.png
        if os.path.exists(floor_path):
            ground = pygame.image.load(floor_path).convert_alpha()
            gw, gh = ground.get_size()
            wcount = 0
            for row in range(border, map_rows - border):
                for col in range(border, map_cols - border):
                    px = col * TILESIZE + TILESIZE // 2
                    py = row * TILESIZE + TILESIZE // 2
                    if px < gw and py < gh:
                        c = ground.get_at((px, py))
                        if c[2] > c[0] and c[2] > c[1] and c[2] > 60:
                            MapManager._water_tiles_cache.append((col * TILESIZE, row * TILESIZE))
                            Tile((col * TILESIZE, row * TILESIZE), [level.obstacle_sprites], SPRITE_INVISIBLE)
                            wcount += 1
            print(f'[MAP] {wcount} water + {len(MapManager._water_tiles_cache)-wcount} border tiles blocked ({map_cols}x{map_rows})')
        else:
            print(f'[MAP] {len(MapManager._water_tiles_cache)} border tiles blocked ({map_cols}x{map_rows})')

    def _ensure_safe_spawn(self):
        """Verify player spawn is in a walkable area. If blocked, find nearest open tile."""
        level = self.level
        if not level.player or not level.pathfinding_grid:
            return
        grid = level.pathfinding_grid
        gx, gy = pos_to_grid(level.player.hitbox.center, TILESIZE)
        if 0 <= gy < len(grid) and 0 <= gx < len(grid[0]) and grid[gy][gx] == 0:
            return
        for radius in range(1, max(len(grid), len(grid[0]) if grid else 0) + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = gx + dx, gy + dy
                    if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == 0:
                        safe_pos = grid_to_pos((nx, ny), TILESIZE)
                        level.player.pos.x, level.player.pos.y = safe_pos
                        level.player.rect.center = safe_pos
                        level.player.hitbox.center = safe_pos
                        return

