"""Map loading + water detection + safe spawn + save-state."""
import os
import pygame
from settings import TILESIZE
from tile import Tile
from player import Player
from enemy import Enemy
from support import import_csv_layout, import_folder, get_path
from constants import (
    LAYER_BOUNDARY, LAYER_GRASS, LAYER_OBJECT, LAYER_ENTITIES,
    SPRITE_GRASS, SPRITE_OBJECT, SPRITE_INVISIBLE, SPRITE_ENEMY,
    ENTITY_PLAYER_SPAWN, ENTITY_MONSTER_MAP,
)
from pathfinding_utils import build_grid
from random import choice


class MapManager:
    def __init__(self, level):
        self.level = level
        self.player = None
        self.pathfinding_grid = None

    def load_map(self, map_id='default', loaded_data=None):
        layouts = self._load_layouts(map_id)
        graphics = {
            'grass': import_folder('../graphics/grass'),
            'objects': import_folder('../graphics/objects'),
        }

        # Water detection
        water_tiles = self._detect_water()

        # Track saved grass state
        destroyed_grass = set()
        if loaded_data and 'destroyed_grass' in loaded_data:
            for g in loaded_data['destroyed_grass']:
                destroyed_grass.add((g['x'], g['y']))

        # Map pixel dimensions from boundary layer
        boundary_layout = layouts[LAYER_BOUNDARY]
        map_rows = len(boundary_layout)
        map_cols = len(boundary_layout[0]) if map_rows > 0 else 0

        for style, layout in layouts.items():
            for row_idx, row in enumerate(layout):
                for col_idx, col in enumerate(row):
                    if col == '-1':
                        continue
                    x, y = col_idx * TILESIZE, row_idx * TILESIZE
                    is_water = (col_idx, row_idx) in water_tiles
                    is_perimeter = (row_idx < 2 or row_idx >= map_rows - 2 or
                                    col_idx < 2 or col_idx >= map_cols - 2)

                    if style == LAYER_BOUNDARY or is_perimeter or \
                       (style == LAYER_GRASS and is_water):
                        Tile((x, y), [self.level.obstacle_sprites],
                             SPRITE_INVISIBLE)
                    elif style == LAYER_GRASS:
                        if (x, y) in destroyed_grass:
                            continue
                        img = choice(graphics['grass'])
                        Tile((x, y),
                             [self.level.visible_sprites,
                              self.level.obstacle_sprites,
                              self.level.combat.attackable_sprites],
                             SPRITE_GRASS, img)
                    elif style == LAYER_OBJECT:
                        surf = graphics['objects'][int(col)]
                        Tile((x, y),
                             [self.level.visible_sprites,
                              self.level.obstacle_sprites],
                             SPRITE_OBJECT, surf)

        # Pathfinding grid using actual map pixel dimensions
        map_pixel_w = map_cols * TILESIZE
        map_pixel_h = map_rows * TILESIZE
        self.pathfinding_grid = build_grid(
            map_pixel_w, map_pixel_h, TILESIZE,
            self.level.obstacle_sprites)

        # Track saved enemy state
        defeated = set()
        if loaded_data and 'defeated_enemies' in loaded_data:
            for e in loaded_data['defeated_enemies']:
                defeated.add((e['x'], e['y']))

        self._spawn_entities(layouts.get(LAYER_ENTITIES, []),
                             defeated, loaded_data)

    def _detect_water(self):
        water = set()
        try:
            ground = pygame.image.load(
                get_path('../graphics/tilemap/ground.png')).convert()
            gw = ground.get_width() // TILESIZE
            gh = ground.get_height() // TILESIZE
            for r in range(gh):
                for c in range(gw):
                    cx = c * TILESIZE + TILESIZE // 2
                    cy = r * TILESIZE + TILESIZE // 2
                    if cx < ground.get_width() and cy < ground.get_height():
                        pixel = ground.get_at((cx, cy))
                        if pixel[2] > pixel[0] and pixel[2] > pixel[1] and pixel[2] > 60:
                            water.add((c, r))
        except Exception:
            pass
        return water

    def _load_layouts(self, map_id='default'):
        def load(layer):
            path = f'../data/map/map_{map_id}_{layer}.csv'
            if not os.path.exists(path):
                path = f'../data/map/map_{layer}.csv'
            return import_csv_layout(path)
        return {
            LAYER_BOUNDARY: load(LAYER_BOUNDARY),
            LAYER_GRASS: load(LAYER_GRASS),
            LAYER_OBJECT: load(LAYER_OBJECT),
            LAYER_ENTITIES: load(LAYER_ENTITIES),
        }

    def _spawn_entities(self, layout, defeated, loaded_data):
        for row_idx, row in enumerate(layout):
            for col_idx, col in enumerate(row):
                if col == '-1':
                    continue
                x, y = col_idx * TILESIZE, row_idx * TILESIZE

                if col == ENTITY_PLAYER_SPAWN:
                    x, y = self._ensure_safe_spawn(x, y)
                    self.player = Player(
                        (x, y), [self.level.visible_sprites],
                        self.level.obstacle_sprites,
                        self.level.create_attack,
                        self.level.destroy_attack,
                        self.level.create_magic)
                    if loaded_data and 'player' in loaded_data:
                        self.player.from_dict(loaded_data['player'])
                elif col in ENTITY_MONSTER_MAP:
                    if (x, y) not in defeated:
                        name = ENTITY_MONSTER_MAP[col]
                        Enemy(
                            name, (x, y),
                            [self.level.visible_sprites,
                             self.level.combat.attackable_sprites],
                            self.level.obstacle_sprites,
                            self.level.damage_player,
                            self.level.trigger_death_particles,
                            self.level.add_exp,
                            trigger_exp_particles=self.level.trigger_exp_particles,
                            pathfinding_grid=self.pathfinding_grid)

    def _ensure_safe_spawn(self, x, y):
        if self.pathfinding_grid is None:
            return x, y
        gx, gy = x // TILESIZE, y // TILESIZE
        gw = len(self.pathfinding_grid[0]) if self.pathfinding_grid else 0
        gh = len(self.pathfinding_grid)
        if 0 <= gx < gw and 0 <= gy < gh and self.pathfinding_grid[gy][gx] == 0:
            return x, y
        for radius in range(1, 15):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < gw and 0 <= ny < gh and \
                       self.pathfinding_grid[ny][nx] == 0:
                        return nx * TILESIZE, ny * TILESIZE
        return x, y
