import pygame
from weapon import Weapon
from ui import UI
from particles import AnimationPlayer
from magic import MagicPlayer
from map_manager import MapManager
from support import get_path
from constants import SPRITE_GRASS, SPRITE_ENEMY
from random import randint


class Level:
    def __init__(self, loaded_data=None):
        self.display_surface = pygame.display.get_surface()

        # sprite groups
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()

        # attack
        self.current_attack = None
        self.attack_sprites = pygame.sprite.Group()
        self.attackable_sprites = pygame.sprite.Group()

        # particles & magic
        self.animation_player = AnimationPlayer()
        self.magic_player = MagicPlayer(self.animation_player)

        # UI
        self.ui = UI()

        # floating text
        self.floating_texts = []

        # map
        player_callbacks = {
            'create_attack': self.create_attack,
            'destroy_attack': self.destroy_attack,
            'damage_player': self.damage_player,
            'add_exp': self.add_exp,
            'trigger_death_particles': self.trigger_death_particles,
        }
        self.map_manager = MapManager(
            self.visible_sprites, self.obstacle_sprites,
            self.attackable_sprites, player_callbacks)
        self.map_manager.load_map(loaded_data)
        self.player = self.map_manager.player

        # attach magic callback after player created
        self.player.create_magic = self.create_magic

    def create_attack(self):
        self.current_attack = Weapon(
            self.player,
            [self.visible_sprites, self.attack_sprites],
            self.player.weapon)

    def destroy_attack(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def create_magic(self, style, strength, cost):
        if style == 'heal':
            self.magic_player.heal(
                self.player, strength, cost, [self.visible_sprites])
        elif style == 'flame':
            self.magic_player.flame(
                self.player, cost, [self.visible_sprites, self.attack_sprites])

    def player_attack_logic(self):
        if self.attack_sprites:
            for attack_sprite in self.attack_sprites:
                hits = pygame.sprite.spritecollide(
                    attack_sprite, self.attackable_sprites, False)
                for target in hits:
                    if target.sprite_type == SPRITE_GRASS:
                        pos = target.rect.center
                        offset = pygame.math.Vector2(0, 75)
                        for _ in range(3):
                            self.animation_player.create_grass_particles(
                                pos - offset, [self.visible_sprites])
                        target.kill()
                    elif target.sprite_type == SPRITE_ENEMY:
                        damage = self.player.attack_damage
                        # flame magic from attack_sprites
                        if attack_sprite.sprite_type == 'magic':
                            damage = 5  # per flame particle
                        target.get_damage(damage)
                        self.spawn_hit_sparks(target.rect.center)

    def damage_player(self, amount):
        if self.player.vulnerable:
            self.player.take_damage(amount)

    def add_exp(self, amount):
        self.player.add_exp(amount)
        self.spawn_floating_text(
            f'+{amount} EXP', self.player.rect.midtop, (255, 255, 100))

    def trigger_death_particles(self, pos, particle_type):
        self.animation_player.create_particles(
            particle_type, pos, self.visible_sprites)

    def spawn_hit_sparks(self, pos):
        """Spawn hit sparks on enemy."""
        for _ in range(6):
            x = pos[0] + randint(-15, 15)
            y = pos[1] + randint(-15, 15)
            self.animation_player.create_particles(
                'sparkle', (x, y), [self.visible_sprites])

    def spawn_floating_text(self, text, pos, color):
        self.floating_texts.append({
            'text': text, 'pos': pygame.math.Vector2(pos),
            'color': color, 'life': 1.0, 'speed': -60})

    def _update_floating_texts(self, dt):
        font = pygame.font.Font(None, 22)
        alive = []
        for ft in self.floating_texts:
            ft['life'] -= dt
            if ft['life'] <= 0:
                continue
            ft['pos'].y += ft['speed'] * dt
            alpha = int(255 * ft['life'])
            surf = font.render(ft['text'], False, ft['color'])
            surf.set_alpha(alpha)
            offset = self.visible_sprites.offset
            r = surf.get_rect(center=(ft['pos'].x - offset.x,
                                       ft['pos'].y - offset.y))
            self.display_surface.blit(surf, r)
            alive.append(ft)
        self.floating_texts = alive

    def all_enemies_dead(self):
        for sprite in self.visible_sprites:
            if hasattr(sprite, 'sprite_type') and sprite.sprite_type == SPRITE_ENEMY:
                return False
        return True

    def get_savable_state(self):
        return self.map_manager.get_savable_state(self.player)

    def run(self, dt):
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update(dt)
        self.visible_sprites.enemy_update(self.player)
        self.player_attack_logic()
        self._update_floating_texts(dt)
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
