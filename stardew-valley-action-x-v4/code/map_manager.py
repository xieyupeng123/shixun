"""Map loading — extracted from level.py."""
import os
import pygame
from settings import TILESIZE, WIDTH, HEIGHT
from tile import Tile
from player import Player
from enemy import Enemy
from support import import_csv_layout, import_folder
from constants import (
    LAYER_BOUNDARY, LAYER_GRASS, LAYER_OBJECT, LAYER_ENTITIES,
    SPRITE_GRASS, SPRITE_OBJECT, SPRITE_INVISIBLE,
    ENTITY_PLAYER_SPAWN, ENTITY_SLIME,
)
from pathfinding_utils import build_grid
from random import choice


class MapManager:
    """Handles map loading, tile placement, and entity spawning."""

    def __init__(self, visible_sprites, obstacle_sprites,
                 attackable_sprites, player_callbacks):
        self.visible_sprites = visible_sprites
        self.obstacle_sprites = obstacle_sprites
        self.attackable_sprites = attackable_sprites
        self.create_attack = player_callbacks['create_attack']
        self.destroy_attack = player_callbacks['destroy_attack']
        self.damage_player = player_callbacks['damage_player']
        self.add_exp = player_callbacks['add_exp']
        self.player = None
        self.pathfinding_grid = None

    def load_map(self, map_id='default'):
        layouts = self._load_layouts(map_id)
        graphics = {
            'grass': import_folder('../graphics/grass'),
            'objects': import_folder('../graphics/objects'),
        }

        for style, layout in layouts.items():
            for row_idx, row in enumerate(layout):
                for col_idx, col in enumerate(row):
                    if col == '-1':
                        continue
                    x = col_idx * TILESIZE
                    y = row_idx * TILESIZE
                    self._place_tile(style, col, x, y, graphics)

        self.pathfinding_grid = build_grid(
            WIDTH, HEIGHT, TILESIZE, self.obstacle_sprites)

        self._spawn_entities(layouts.get(LAYER_ENTITIES, []))

    def _load_layouts(self, map_id):
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

    def _place_tile(self, style, col, x, y, graphics):
        if style == LAYER_BOUNDARY:
            Tile((x, y), [self.obstacle_sprites], SPRITE_INVISIBLE)
        elif style == LAYER_GRASS:
            img = choice(graphics['grass'])
            Tile((x, y),
                 [self.visible_sprites, self.obstacle_sprites,
                  self.attackable_sprites], SPRITE_GRASS, img)
        elif style == LAYER_OBJECT:
            surf = graphics['objects'][int(col)]
            Tile((x, y),
                 [self.visible_sprites, self.obstacle_sprites],
                 SPRITE_OBJECT, surf)

    def _spawn_entities(self, layout):
        for row_idx, row in enumerate(layout):
            for col_idx, col in enumerate(row):
                if col == '-1':
                    continue
                x = col_idx * TILESIZE
                y = row_idx * TILESIZE

                if col == ENTITY_PLAYER_SPAWN:
                    self.player = Player(
                        (x, y), [self.visible_sprites],
                        self.obstacle_sprites,
                        self.create_attack, self.destroy_attack)
                elif col == ENTITY_SLIME:
                    Enemy(
                        'slime', (x, y),
                        [self.visible_sprites, self.attackable_sprites],
                        self.obstacle_sprites,
                        self.damage_player, self.add_exp,
                        pathfinding_grid=self.pathfinding_grid)
