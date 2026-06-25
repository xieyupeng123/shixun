import pygame
from settings import TILESIZE
from tile import Tile
from player import Player
from weapon import Weapon
from enemy import Enemy
from ui import UI
from particles import spawn_hit_particles
from support import get_path, import_csv_layout, import_folder
from random import choice


class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()

        # sprite groups
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()

        # attack
        self.current_attack = None
        self.attack_sprites = pygame.sprite.Group()
        self.attackable_sprites = pygame.sprite.Group()

        # particles
        self.particle_sprites = pygame.sprite.Group()

        # player
        self.player = None

        # UI
        self.ui = UI()

        # build map
        self.create_map()

    def create_map(self):
        layouts = {
            'boundary': import_csv_layout('../data/map/map_FloorBlocks.csv'),
            'grass': import_csv_layout('../data/map/map_Grass.csv'),
            'object': import_csv_layout('../data/map/map_Objects.csv'),
            'entities': import_csv_layout('../data/map/map_Entities.csv'),
        }

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

                    if style == 'boundary':
                        Tile((x, y), [self.obstacle_sprites], 'invisible')

                    if style == 'grass':
                        random_grass_image = choice(graphics['grass'])
                        Tile((x, y),
                             [self.visible_sprites, self.obstacle_sprites,
                              self.attackable_sprites],
                             'grass', random_grass_image)

                    if style == 'object':
                        surf = graphics['objects'][int(col)]
                        Tile((x, y),
                             [self.visible_sprites, self.obstacle_sprites],
                             'object', surf)

        # Spawn entities
        entities_layout = layouts['entities']
        for row_idx, row in enumerate(entities_layout):
            for col_idx, col in enumerate(row):
                if col == '-1':
                    continue
                x = col_idx * TILESIZE
                y = row_idx * TILESIZE

                if col == '394':  # Player spawn
                    self.player = Player(
                        (x, y), [self.visible_sprites],
                        self.obstacle_sprites,
                        self.create_attack, self.destroy_attack)
                elif col == '390':  # Slime enemy
                    Enemy('slime', (x, y),
                          [self.visible_sprites, self.attackable_sprites],
                          self.obstacle_sprites,
                          self.damage_player, self.add_exp)

    def create_attack(self):
        self.current_attack = Weapon(
            self.player, [self.visible_sprites, self.attack_sprites])

    def destroy_attack(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def player_attack_logic(self):
        if self.attack_sprites:
            for attack_sprite in self.attack_sprites:
                collision_sprites = pygame.sprite.spritecollide(
                    attack_sprite, self.attackable_sprites, False)
                if collision_sprites:
                    for target in collision_sprites:
                        if target.sprite_type == 'grass':
                            spawn_hit_particles(
                                target.rect.center, [self.particle_sprites])
                            target.kill()
                        elif target.sprite_type == 'enemy':
                            spawn_hit_particles(
                                target.rect.center, [self.particle_sprites])
                            target.get_damage(self.player.attack_damage)

    def damage_player(self, amount):
        if self.player.vulnerable:
            self.player.take_damage(amount)

    def add_exp(self, amount):
        self.player.add_exp(amount)

    def run(self, dt):
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update(dt)
        self.visible_sprites.enemy_update(self.player)
        self.particle_sprites.update(dt)

        # Draw particles through camera
        for sprite in self.particle_sprites:
            offset = self.visible_sprites.offset
            pos = sprite.rect.topleft - offset
            self.display_surface.blit(sprite.image, pos)

        self.player_attack_logic()
        self.ui.display(self.player)


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

        floor_path = get_path('../graphics/tilemap/ground.png')
        self.floor_surf = pygame.image.load(floor_path).convert()
        self.floor_rect = self.floor_surf.get_rect(topleft=(0, 0))

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        floor_offset_pos = self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf, floor_offset_pos)

        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            offset_rect = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_rect)

    def enemy_update(self, player):
        enemy_sprites = [s for s in self.sprites()
                         if hasattr(s, 'sprite_type') and s.sprite_type == 'enemy']
        for enemy in enemy_sprites:
            enemy.enemy_update(player)
