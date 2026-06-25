"""Map loading + entity spawning with save-state awareness."""
import os
from settings import TILESIZE, WIDTH, HEIGHT
from tile import Tile
from player import Player
from enemy import Enemy
from support import import_csv_layout, import_folder
from constants import (
    LAYER_BOUNDARY, LAYER_GRASS, LAYER_OBJECT, LAYER_ENTITIES,
    SPRITE_GRASS, SPRITE_OBJECT, SPRITE_INVISIBLE,
    ENTITY_PLAYER_SPAWN, ENTITY_MONSTER_MAP,
)
from pathfinding_utils import build_grid
from random import choice


class MapManager:
    def __init__(self, visible_sprites, obstacle_sprites,
                 attackable_sprites, player_callbacks):
        self.visible_sprites = visible_sprites
        self.obstacle_sprites = obstacle_sprites
        self.attackable_sprites = attackable_sprites
        self.create_attack = player_callbacks['create_attack']
        self.destroy_attack = player_callbacks['destroy_attack']
        self.damage_player = player_callbacks['damage_player']
        self.add_exp = player_callbacks['add_exp']
        self.trigger_death_particles = player_callbacks.get('trigger_death_particles')
        self.player = None
        self.pathfinding_grid = None

    def load_map(self, loaded_data=None):
        layouts = self._load_layouts()
        graphics = {
            'grass': import_folder('../graphics/grass'),
            'objects': import_folder('../graphics/objects'),
        }

        # Track destroyed grass from save
        destroyed_grass = set()
        if loaded_data and 'destroyed_grass' in loaded_data:
            for g in loaded_data['destroyed_grass']:
                destroyed_grass.add((g['x'], g['y']))

        for style, layout in layouts.items():
            for row_idx, row in enumerate(layout):
                for col_idx, col in enumerate(row):
                    if col == '-1':
                        continue
                    x = col_idx * TILESIZE
                    y = row_idx * TILESIZE
                    if style == LAYER_BOUNDARY:
                        Tile((x, y), [self.obstacle_sprites], SPRITE_INVISIBLE)
                    elif style == LAYER_GRASS:
                        if (x, y) in destroyed_grass:
                            continue
                        img = choice(graphics['grass'])
                        Tile((x, y),
                             [self.visible_sprites, self.obstacle_sprites,
                              self.attackable_sprites], SPRITE_GRASS, img)
                    elif style == LAYER_OBJECT:
                        surf = graphics['objects'][int(col)]
                        Tile((x, y),
                             [self.visible_sprites, self.obstacle_sprites],
                             SPRITE_OBJECT, surf)

        self.pathfinding_grid = build_grid(
            WIDTH, HEIGHT, TILESIZE, self.obstacle_sprites)

        # Track defeated enemies from save
        defeated = set()
        if loaded_data and 'defeated_enemies' in loaded_data:
            for e in loaded_data['defeated_enemies']:
                defeated.add((e['x'], e['y']))

        self._spawn_entities(layouts.get(LAYER_ENTITIES, []), defeated, loaded_data)

    def _load_layouts(self):
        def load(layer):
            path = f'../data/map/map_{layer}.csv'
            return import_csv_layout(path)
        return {
            LAYER_BOUNDARY: load(LAYER_BOUNDARY),
            LAYER_GRASS: load(LAYER_GRASS),
            LAYER_OBJECT: load(LAYER_OBJECT),
            LAYER_ENTITIES: load(LAYER_ENTITIES),
        }

    def _spawn_entities(self, layout, defeated, loaded_data):
        player_spawned = False
        for row_idx, row in enumerate(layout):
            for col_idx, col in enumerate(row):
                if col == '-1':
                    continue
                x = col_idx * TILESIZE
                y = row_idx * TILESIZE

                if col == ENTITY_PLAYER_SPAWN:
                    if not player_spawned:
                        self.player = Player(
                            (x, y), [self.visible_sprites],
                            self.obstacle_sprites,
                            self.create_attack, self.destroy_attack)
                        if loaded_data and 'player' in loaded_data:
                            self.player.from_dict(loaded_data['player'])
                        player_spawned = True
                elif col in ENTITY_MONSTER_MAP:
                    if (x, y) not in defeated:
                        name = ENTITY_MONSTER_MAP[col]
                        Enemy(
                            name, (x, y),
                            [self.visible_sprites, self.attackable_sprites],
                            self.obstacle_sprites,
                            self.damage_player, self.add_exp,
                            trigger_death_particles=self.trigger_death_particles,
                            pathfinding_grid=self.pathfinding_grid)

    def get_savable_state(self, player):
        defeated = []
        destroyed = []
        for sprite in self.attackable_sprites:
            if not sprite.alive():
                if hasattr(sprite, 'sprite_type'):
                    if sprite.sprite_type == SPRITE_GRASS:
                        destroyed.append(
                            {'x': sprite.rect.x, 'y': sprite.rect.y})
        for sprite in self.visible_sprites:
            if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'enemy':
                if not sprite.alive():
                    defeated.append(
                        {'x': sprite.rect.x, 'y': sprite.rect.y})
        return {
            'player': player.to_dict(),
            'defeated_enemies': defeated,
            'destroyed_grass': destroyed,
        }
