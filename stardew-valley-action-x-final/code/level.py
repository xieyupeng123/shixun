import pygame
from settings import TILESIZE
from support import get_path
from random import randint
from weapon import Weapon
from ui import UI
from enemy import Enemy
from particles import AnimationPlayer
from magic import MagicPlayer
from upgrade import Upgrade
from map_manager import MapManager
from music_state import MusicState


# ── Combat Manager ───────────────────────────────────────────────────
class CombatManager:
    """Handles weapon/magic creation, attack collision, and player damage.

    Extracted from Level to separate combat concerns from map logic.
    """

    def __init__(self, level):
        self.level = level
        self.current_attack = None
        self.attack_sprites = pygame.sprite.Group()
        self.attackable_sprites = pygame.sprite.Group()

    def create_attack(self):
        self.current_attack = Weapon(
            self.level.player, [self.level.visible_sprites, self.attack_sprites])

    def create_magic(self, style, strength, cost):
        if style == 'heal':
            self.level.magic_player.heal(
                self.level.player, strength, cost, [self.level.visible_sprites])
        if style == 'flame':
            self.level.magic_player.flame(
                self.level.player, cost,
                [self.level.visible_sprites, self.attack_sprites])

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
                    for target_sprite in collision_sprites:
                        if target_sprite.sprite_type == 'grass':
                            pos = target_sprite.rect.center
                            self.level.destroyed_grass.append(
                                {'x': pos[0], 'y': pos[1]})
                            offset = pygame.math.Vector2(0, 75)
                            for leaf in range(randint(3, 6)):
                                self.level.animation_player.create_grass_particles(
                                    pos - offset, [self.level.visible_sprites])
                            target_sprite.kill()
                        else:
                            target_sprite.get_damage(
                                self.level.player, attack_sprite.sprite_type)

    def damage_player(self, amount, attack_type):
        player = self.level.player
        if player.invincible:
            return
        if player.vulnerable:
            player.health -= amount
            player.vulnerable = False
            player.hurt_time = pygame.time.get_ticks()
            self.level.animation_player.create_particles(
                attack_type, player.rect.center,
                [self.level.visible_sprites])


# ── Boss Manager ─────────────────────────────────────────────────────
class BossManager:
    """Manages boss spawning, phase transitions, and victory detection.

    Boss spawns at a fixed CSV marker position. Each kill respawns the boss
    in the next phase (3 phases total). Killing all 3 triggers victory.
    """

    def __init__(self, level):
        self.level = level
        self.boss = None
        self.boss_kills = 0
        self._boss_spawn_pos = None
        self._trigger_victory = False

    def spawn_boss(self, phase):
        """Spawn boss at the fixed 392 marker position."""
        if self._boss_spawn_pos is None:
            return
        # Kill old boss if exists
        if self.boss and self.boss.alive():
            self.boss.kill()
        self.boss = Enemy(
            'raccoon', self._boss_spawn_pos,
            [self.level.visible_sprites, self.level.combat.attackable_sprites],
            self.level.obstacle_sprites,
            self.level.combat.damage_player,
            self.level.trigger_death_particles,
            self.level.add_exp,
            trigger_exp_particles=lambda enemy_pos, player_pos, exp_amount=0, level=self.level:
                level.trigger_exp_particles(enemy_pos, player_pos, exp_amount),
            pathfinding_grid=self.level.pathfinding_grid,
            tile_size=TILESIZE,
            is_boss=True,
            boss_phase=phase,
            on_boss_killed=self._on_boss_killed,
        )

    def _on_boss_killed(self, death_pos):
        """Called when the boss is killed. Respawn next phase at same position."""
        self.boss_kills += 1
        self.boss = None

        if self.boss_kills >= 3:
            self._trigger_victory = True
            return

        # Spawn next phase at the same fixed position
        next_phase = self.boss_kills + 1
        self.spawn_boss(phase=next_phase)


# ── Map Renderer ─────────────────────────────────────────────────────
class MapRenderer:
    """Draws the fullscreen world map overlay (press M to toggle).

    Shows walkable/obstacle grid, enemy positions (red dots), boss (red X),
    and player position (green dot). Completely extracted from Level.
    """

    def __init__(self, level):
        self.level = level

    def draw(self):
        """Draw a FULLSCREEN map overlay showing the entire world."""
        level = self.level
        grid = level.pathfinding_grid
        if not grid:
            return
        grid_h = len(grid)
        grid_w = len(grid[0]) if grid_h > 0 else 0
        if grid_w == 0 or grid_h == 0:
            return

        display_surface = level.display_surface
        sw, sh = display_surface.get_size()
        margin = 40
        map_width = sw - margin * 2
        map_height = sh - margin * 2 - 50
        cell_w = map_width / grid_w
        cell_h = map_height / grid_h
        margin_x = margin
        margin_y = margin + 45

        dark = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 200))
        display_surface.blit(dark, (0, 0))

        title_font = pygame.font.Font(None, 36)
        title = title_font.render("WORLD MAP (M to close)", True, (255, 215, 0))
        display_surface.blit(title, (margin_x, margin_y - 40))

        for row in range(grid_h):
            for col in range(grid_w):
                x = margin_x + col * cell_w
                y = margin_y + row * cell_h
                if grid[row][col] == 1:
                    color = (50, 50, 50, 220)
                else:
                    color = (80, 130, 80, 140)
                cell_rect = pygame.Rect(x, y, cell_w + 0.5, cell_h + 0.5)
                pygame.draw.rect(display_surface, color, cell_rect)

        # Draw enemies (boss gets BIG RED X)
        for sprite in level.combat.attackable_sprites:
            if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'enemy':
                ex = int(margin_x + (sprite.rect.centerx / TILESIZE) * cell_w)
                ey = int(margin_y + (sprite.rect.centery / TILESIZE) * cell_h)
                if getattr(sprite, 'is_boss', False):
                    boss_pulse = (pygame.time.get_ticks() // 300) % 2
                    size = 24 if boss_pulse else 18
                    pygame.draw.circle(display_surface, (255, 0, 0, 80), (ex, ey), size + 10)
                    pygame.draw.circle(display_surface, (255, 0, 0, 40), (ex, ey), size + 18)
                    dx = size
                    pygame.draw.line(display_surface, (255, 0, 0), (ex-dx, ey-dx), (ex+dx, ey+dx), 4)
                    pygame.draw.line(display_surface, (255, 0, 0), (ex+dx, ey-dx), (ex-dx, ey+dx), 4)
                    pygame.draw.line(display_surface, (255, 255, 0), (ex-dx, ey-dx), (ex+dx, ey+dx), 2)
                    pygame.draw.line(display_surface, (255, 255, 0), (ex+dx, ey-dx), (ex-dx, ey+dx), 2)
                    label = title_font.render("BOSS", True, (255, 50, 50))
                    lbl_rect = label.get_rect(midbottom=(ex, ey - size - 8))
                    pygame.draw.rect(display_surface, (0, 0, 0, 200), lbl_rect.inflate(10, 6))
                    display_surface.blit(label, lbl_rect)
                else:
                    pygame.draw.circle(display_surface, (255, 0, 0, 80), (ex, ey), 8)
                    pygame.draw.circle(display_surface, (255, 50, 50), (ex, ey), 5)

        # Draw player (GREEN ARROW)
        player = level.player
        px = int(margin_x + (player.rect.centerx / TILESIZE) * cell_w)
        py = int(margin_y + (player.rect.centery / TILESIZE) * cell_h)
        pulse = (pygame.time.get_ticks() // 400) % 2
        psize = 10 if pulse else 8
        pygame.draw.circle(display_surface, (0, 255, 0, 60), (px, py), psize + 8)
        pygame.draw.circle(display_surface, (255, 255, 255), (px, py), psize + 2)
        pygame.draw.circle(display_surface, (0, 255, 0), (px, py), psize)
        you_label = title_font.render("YOU", True, (0, 255, 0))
        you_rect = you_label.get_rect(midbottom=(px, py - psize - 8))
        pygame.draw.rect(display_surface, (0, 0, 0, 200), you_rect.inflate(8, 4))
        display_surface.blit(you_label, you_rect)

        # Info at bottom
        coord_font = pygame.font.Font(None, 22)
        boss_kills = level.boss.boss_kills if level.boss else 0
        info = f"POS: ({int(player.rect.centerx//TILESIZE)}, {int(player.rect.centery//TILESIZE)})  |  Boss: {boss_kills}/3"
        info_text = coord_font.render(info, True, (200, 200, 200))
        display_surface.blit(info_text, (margin_x, margin_y + map_height + 8))

        # Legend
        lx = margin_x + map_width - 150
        ly = margin_y + map_height + 4
        legend_font = pygame.font.Font(None, 18)
        pygame.draw.circle(display_surface, (0, 255, 0), (lx + 6, ly + 8), 5)
        display_surface.blit(legend_font.render("You", True, (200, 200, 200)), (lx + 16, ly))
        pygame.draw.circle(display_surface, (255, 50, 50), (lx + 6, ly + 28), 5)
        display_surface.blit(legend_font.render("Enemy", True, (200, 200, 200)), (lx + 16, ly + 20))
        dx2 = 6
        pygame.draw.line(display_surface, (255, 0, 0), (lx+6-dx2, ly+48-dx2), (lx+6+dx2, ly+48+dx2), 3)
        pygame.draw.line(display_surface, (255, 0, 0), (lx+6+dx2, ly+48-dx2), (lx+6-dx2, ly+48+dx2), 3)
        display_surface.blit(legend_font.render("BOSS", True, (255, 0, 0)), (lx + 16, ly + 40))

        border_rect = pygame.Rect(margin_x, margin_y, map_width, map_height)
        pygame.draw.rect(display_surface, (255, 215, 0), border_rect, 3)


# ── Level ────────────────────────────────────────────────────────────
class Level:
    """Game level orchestrator.

    Delegates specific responsibilities to manager classes:
    - CombatManager: weapon/magic attacks, collision, damage
    - BossManager: boss spawning, phases, victory
    - MapRenderer: fullscreen world map overlay
    """

    def get_savable_state(self):
        return {
            'player': self.player.to_dict(),
            'defeated_enemies': list(self.killed_enemies),
            'destroyed_grass': list(self.destroyed_grass),
        }

    def __init__(self, map_id, player=None, loaded_data=None, player_spawn_pos=None):
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.game_paused = False
        self.show_map = False

        # sprite group setup
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()

        # managers
        self.combat = CombatManager(self)
        self.boss = BossManager(self)
        self.map_renderer = MapRenderer(self)

        # player setup
        self.player = player
        if player is not None and player_spawn_pos is not None:
            self._player_spawn_pos = player_spawn_pos
        elif player is None and player_spawn_pos is not None:
            self._player_spawn_pos = player_spawn_pos
        else:
            self._player_spawn_pos = None

        # Delegate map loading to MapManager
        MapManager(self, map_id, loaded_data).load()

        # user interface
        self.ui = UI()
        self.upgrade = Upgrade(self.player)

        # particles
        self.animation_player = AnimationPlayer()
        self.magic_player = MagicPlayer(self.animation_player)

        # boss music
        self._boss_music_active = False
        self._boss_bgm_path = get_path('../audio/boss_bgm.ogg')

        # tracking for save system
        self.killed_enemies = []
        self.destroyed_grass = []

    # ── Compatibility Properties ──────────────────────────────────────
    # These properties maintain backward compatibility so that main.py
    # and MapManager can access attributes at their original locations.

    @property
    def current_attack(self):
        return self.combat.current_attack

    @current_attack.setter
    def current_attack(self, value):
        self.combat.current_attack = value

    @property
    def attack_sprites(self):
        return self.combat.attack_sprites

    @property
    def attackable_sprites(self):
        return self.combat.attackable_sprites

    @property
    def boss_kills(self):
        return self.boss.boss_kills

    @property
    def _trigger_victory(self):
        return self.boss._trigger_victory

    @property
    def _boss_spawn_pos(self):
        return self.boss._boss_spawn_pos

    @_boss_spawn_pos.setter
    def _boss_spawn_pos(self, value):
        self.boss._boss_spawn_pos = value

    # ── Delegated Methods (for MapManager compatibility) ──────────────

    def _spawn_boss(self, phase):
        self.boss.spawn_boss(phase)

    def create_attack(self):
        self.combat.create_attack()

    def create_magic(self, style, strength, cost):
        self.combat.create_magic(style, strength, cost)

    def destroy_attack(self):
        self.combat.destroy_attack()

    def player_attack_logic(self):
        self.combat.player_attack_logic()

    def damage_player(self, amount, attack_type):
        self.combat.damage_player(amount, attack_type)

    # ── Particle / EXP Callbacks ──────────────────────────────────────

    def trigger_exp_particles(self, enemy_pos, player_pos, exp_amount=0):
        self.animation_player.create_exp_particles(
            enemy_pos, player_pos, self.visible_sprites,
            amount=5, exp_amount=exp_amount)

    def _record_enemy_death(self, pos, monster_name):
        """Record enemy death position for save system (exclude boss)."""
        if monster_name != 'raccoon':
            self.killed_enemies.append({'x': pos[0], 'y': pos[1]})

    def trigger_death_particles(self, pos, particle_type):
        self.animation_player.create_particles(
            particle_type, pos, self.visible_sprites)
        self._record_enemy_death(pos, particle_type)

    def add_exp(self, amount):
        self.player.exp += amount

    # ── UI Toggles ────────────────────────────────────────────────────

    def toggle_menu(self):
        self.game_paused = not self.game_paused

    def toggle_map(self):
        """Toggle the minimap overlay."""
        self.show_map = not self.show_map

    # ── Boss Music ─────────────────────────────────────────────────────

    def _check_boss_music(self):
        """One-way switch: when player first enters boss notice radius (A* range),
        permanently switch to boss music. Short-circuits once state is 1.
        If player is invincible, only set the state — don't play yet."""
        if MusicState.get() == 1:
            return  # already triggered, skip all checks
        boss = self.boss.boss
        if boss and boss.alive():
            boss_vec = pygame.math.Vector2(boss.rect.center)
            player_vec = pygame.math.Vector2(self.player.rect.center)
            dist = (player_vec - boss_vec).magnitude()
            if dist <= boss.notice_radius:
                MusicState.set(1)
                if not self.player.invincible:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(self._boss_bgm_path)
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)

    # ── Main Game Loop ────────────────────────────────────────────────

    def run(self, dt):
        # update and draw the game
        self.visible_sprites.custom_draw(self.player)
        self.ui.display(self.player,
                        boss_kills=self.boss.boss_kills,
                        boss_sprite=self.boss.boss)

        if self.game_paused:
            self.upgrade.display()
        else:
            self.visible_sprites.update(dt)
            self.visible_sprites.enemy_update(self.player)
            self.player_attack_logic()
            self._check_boss_music()

        # Draw map overlay on top if active
        if self.show_map:
            self.map_renderer.draw()


# ── Y-Sort Camera Group ──────────────────────────────────────────────
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

        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_rect = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_rect)

    def enemy_update(self, player):
        enemy_sprites = [sprite for sprite in self.sprites() if hasattr(
            sprite, 'sprite_type') and sprite.sprite_type == 'enemy']

        for enemy in enemy_sprites:
            enemy.enemy_update(player)
