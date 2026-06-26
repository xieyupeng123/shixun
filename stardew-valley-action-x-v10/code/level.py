import pygame
from settings import TILESIZE
from weapon import Weapon
from ui import UI
from particles import AnimationPlayer, FloatingText
from magic import MagicPlayer
from map_manager import MapManager
from upgrade import Upgrade
from support import get_path
from constants import SPRITE_GRASS, SPRITE_ENEMY
from random import randint


class CombatManager:
    def __init__(self, level):
        self.level = level
        self.current_attack = None
        self.attack_sprites = pygame.sprite.Group()
        self.attackable_sprites = pygame.sprite.Group()
        self.destroyed_grass = []
        self.killed_enemies = []

    def create_attack(self):
        self.current_attack = Weapon(
            self.level.player,
            [self.level.visible_sprites, self.attack_sprites],
            self.level.player.weapon)

    def create_magic(self, style, strength, cost):
        if style == 'heal':
            self.level.magic_player.heal(
                self.level.player, strength, cost,
                [self.level.visible_sprites])
        elif style == 'flame':
            self.level.magic_player.flame(
                self.level.player, cost,
                [self.level.visible_sprites, self.attack_sprites])

    def destroy_attack(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def player_attack_logic(self):
        if not self.attack_sprites:
            return
        for atk in self.attack_sprites:
            hits = pygame.sprite.spritecollide(
                atk, self.attackable_sprites, False)
            for target in hits:
                if target.sprite_type == SPRITE_GRASS:
                    pos = target.rect.center
                    self.destroyed_grass.append({'x': pos[0], 'y': pos[1]})
                    for _ in range(randint(3, 6)):
                        self.level.animation_player.create_grass_particles(
                            pos - pygame.math.Vector2(0, 75),
                            [self.level.visible_sprites])
                    target.kill()
                elif target.sprite_type == SPRITE_ENEMY:
                    dmg = self.level.player.get_full_weapon_damage()
                    if getattr(atk, 'sprite_type', '') == 'magic':
                        dmg = self.level.player.get_full_magic_damage()
                    target.get_damage(dmg)
                    self._spawn_hit_sparks(target.rect.center)

    def damage_player(self, amount, attack_type='slash'):
        player = self.level.player
        if getattr(player, 'invincible', False):
            return
        if player.vulnerable:
            player.take_damage(amount)
            self.level.animation_player.create_particles(
                attack_type, player.rect.center,
                [self.level.visible_sprites])

    def _spawn_hit_sparks(self, pos):
        for _ in range(6):
            sx, sy = pos[0] + randint(-15, 15), pos[1] + randint(-15, 15)
            self.level.animation_player.create_particles(
                'sparkle', (sx, sy), [self.level.visible_sprites])


class BossManager:
    def __init__(self, level):
        self.level = level
        self.boss = None
        self.boss_spawn_pos = None
        self.boss_kills = 0
        self._trigger_victory = False

    def find_boss_spawn(self, layouts):
        for row_idx, row in enumerate(layouts.get('Entities', [])):
            for col_idx, col in enumerate(row):
                if col == '392':
                    self.boss_spawn_pos = (
                        col_idx * TILESIZE, row_idx * TILESIZE)
                    return

    def spawn_boss(self, phase=0):
        if not self.boss_spawn_pos:
            return
        from enemy import Enemy
        self.boss = Enemy(
            'boss', self.boss_spawn_pos,
            [self.level.visible_sprites,
             self.level.combat.attackable_sprites],
            self.level.obstacle_sprites,
            self.level.combat.damage_player,
            self.level.trigger_death_particles,
            self.level.add_exp,
            trigger_exp_particles=self.level.trigger_exp_particles,
            on_boss_killed=self._on_boss_killed,
            pathfinding_grid=self.level.pathfinding_grid)
        if phase > 0:
            self.boss._current_phase = phase
            for _ in range(phase):
                self.boss.speed = int(self.boss.speed * 1.2)

    def _on_boss_killed(self, death_pos):
        self.boss_kills += 1
        if self.boss_kills >= 3:
            self._trigger_victory = True
        else:
            self.spawn_boss(phase=self.boss_kills)


class MapRenderer:
    def __init__(self, level):
        self.level = level

    def draw(self):
        surface = self.level.display_surface
        w, h = surface.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        surface.blit(overlay, (0, 0))

        grid = self.level.pathfinding_grid
        if not grid:
            return
        rows, cols = len(grid), len(grid[0])
        cell = min((w - 80) // cols, (h - 120) // rows, 12)
        off_x = (w - cols * cell) // 2
        off_y = 60

        for r in range(rows):
            for c in range(cols):
                color = (60, 180, 60) if grid[r][c] == 0 else (80, 80, 80)
                pygame.draw.rect(surface, color,
                                 (off_x + c * cell, off_y + r * cell,
                                  cell - 1, cell - 1))

        for spr in self.level.visible_sprites:
            if not hasattr(spr, 'sprite_type'):
                continue
            sx = off_x + int(spr.rect.centerx / TILESIZE * cell)
            sy = off_y + int(spr.rect.centery / TILESIZE * cell)
            if spr.sprite_type == SPRITE_ENEMY:
                is_boss = getattr(spr, 'is_boss', False)
                color = (255, 60, 60) if is_boss else (255, 150, 50)
                size = 6 if is_boss else 3
                t = pygame.time.get_ticks()
                if is_boss:
                    if (t // 300) % 2:
                        pygame.draw.line(surface, color,
                                         (sx - 4, sy - 4), (sx + 4, sy + 4), 2)
                        pygame.draw.line(surface, color,
                                         (sx - 4, sy + 4), (sx + 4, sy - 4), 2)
                    font = pygame.font.Font(None, 16)
                    lbl = font.render('BOSS', False, (255, 50, 50))
                    surface.blit(lbl, (sx + 8, sy - 10))
                else:
                    if (t // 400) % 2:
                        pygame.draw.circle(surface, color, (sx, sy), size)

        p = self.level.player
        px = off_x + int(p.rect.centerx / TILESIZE * cell)
        py = off_y + int(p.rect.centery / TILESIZE * cell)
        t = pygame.time.get_ticks()
        if (t // 300) % 2:
            pygame.draw.circle(surface, (100, 255, 100), (px, py), 5)
            font = pygame.font.Font(None, 16)
            lbl = font.render('YOU', False, (100, 255, 100))
            surface.blit(lbl, (px + 8, py - 10))

        font = pygame.font.Font(None, 20)
        title = font.render('WORLD MAP (M to close)', False, (255, 255, 255))
        surface.blit(title, ((w - title.get_width()) // 2, 15))
        pos_text = font.render(
            f'POS: ({int(p.rect.centerx)}, {int(p.rect.centery)}) | '
            f'Boss: {self.level.boss.boss_kills}/3', False, (200, 200, 200))
        surface.blit(pos_text, ((w - pos_text.get_width()) // 2, h - 30))


class Level:
    def __init__(self, map_id='default', player=None, loaded_data=None):
        self.display_surface = pygame.display.get_surface()

        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()

        self.combat = CombatManager(self)
        self.boss = BossManager(self)
        self.map_renderer = MapRenderer(self)
        self.animation_player = AnimationPlayer()
        self.magic_player = MagicPlayer(self.animation_player)
        self.ui = UI()
        self.upgrade = None

        self.game_paused = False
        self.show_map = False
        self.pathfinding_grid = None

        self.map_manager = MapManager(self)
        self.map_manager.load_map(map_id, loaded_data)
        self.player = self.map_manager.player
        self.pathfinding_grid = self.map_manager.pathfinding_grid

        if self.player:
            self.player.create_magic = self.combat.create_magic
            self.upgrade = Upgrade(self.player)

        self.boss.find_boss_spawn(
            self.map_manager._load_layouts(map_id))
        self.boss.spawn_boss(phase=0)

    def create_attack(self):
        self.combat.create_attack()

    def destroy_attack(self):
        self.combat.destroy_attack()

    def create_magic(self, style, strength, cost):
        self.combat.create_magic(style, strength, cost)

    def damage_player(self, amount, attack_type='slash'):
        self.combat.damage_player(amount, attack_type)

    def add_exp(self, amount):
        self.player.add_exp(amount)
        FloatingText(f'+{amount} EXP', self.player.rect.midtop,
                     [self.visible_sprites])

    def trigger_exp_particles(self, enemy_pos, player_pos, exp_amount=0):
        self.animation_player.create_exp_particles(
            enemy_pos, player_pos, [self.visible_sprites], amount=5)

    def trigger_death_particles(self, pos, particle_type):
        self.animation_player.create_particles(
            particle_type, pos, [self.visible_sprites])

    def toggle_menu(self):
        self.game_paused = not self.game_paused

    def toggle_map(self):
        self.show_map = not self.show_map

    def get_savable_state(self):
        return {
            'player': self.player.to_dict(),
            'defeated_enemies': list(self.combat.killed_enemies),
            'destroyed_grass': list(self.combat.destroyed_grass),
        }

    def run(self, dt):
        self.visible_sprites.custom_draw(self.player)
        self.ui.display(self.player,
                        boss_kills=self.boss.boss_kills,
                        boss_sprite=self.boss.boss)

        if self.game_paused:
            self.upgrade.display()
        else:
            self.visible_sprites.update(dt)
            self.visible_sprites.enemy_update(self.player)
            self.combat.player_attack_logic()

        if self.show_map:
            self.map_renderer.draw()


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
        self.display_surface.blit(
            self.floor_surf, self.floor_rect.topleft - self.offset)
        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            self.display_surface.blit(
                sprite.image, sprite.rect.topleft - self.offset)

    def enemy_update(self, player):
        for sprite in self.sprites():
            if hasattr(sprite, 'sprite_type') and \
               sprite.sprite_type == SPRITE_ENEMY:
                sprite.enemy_update(player)
