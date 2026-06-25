import pygame
from weapon import Weapon
from ui import UI
from particles import spawn_hit_particles
from map_manager import MapManager
from support import get_path
from constants import SPRITE_GRASS, SPRITE_ENEMY


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

        # UI
        self.ui = UI()

        # map manager
        player_callbacks = {
            'create_attack': self.create_attack,
            'destroy_attack': self.destroy_attack,
            'damage_player': self.damage_player,
            'add_exp': self.add_exp,
        }
        self.map_manager = MapManager(
            self.visible_sprites, self.obstacle_sprites,
            self.attackable_sprites, player_callbacks)
        self.map_manager.load_map('default')
        self.player = self.map_manager.player

    def create_attack(self):
        weapon_name = self.player.weapon
        self.current_attack = Weapon(
            self.player,
            [self.visible_sprites, self.attack_sprites],
            weapon_name)

    def destroy_attack(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def player_attack_logic(self):
        if self.attack_sprites:
            for attack_sprite in self.attack_sprites:
                hits = pygame.sprite.spritecollide(
                    attack_sprite, self.attackable_sprites, False)
                for target in hits:
                    if target.sprite_type == SPRITE_GRASS:
                        spawn_hit_particles(
                            target.rect.center, [self.particle_sprites])
                        target.kill()
                    elif target.sprite_type == SPRITE_ENEMY:
                        spawn_hit_particles(
                            target.rect.center, [self.particle_sprites])
                        target.get_damage(self.player.attack_damage)

    def damage_player(self, amount):
        if self.player.vulnerable:
            self.player.take_damage(amount)

    def add_exp(self, amount):
        self.player.add_exp(amount)

    def all_enemies_dead(self):
        for sprite in self.visible_sprites.sprites():
            if hasattr(sprite, 'sprite_type') and sprite.sprite_type == SPRITE_ENEMY:
                return False
        return True

    def run(self, dt):
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update(dt)
        self.visible_sprites.enemy_update(self.player)
        self.particle_sprites.update(dt)

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
        for sprite in self.sprites():
            if hasattr(sprite, 'sprite_type') and sprite.sprite_type == SPRITE_ENEMY:
                sprite.enemy_update(player)
