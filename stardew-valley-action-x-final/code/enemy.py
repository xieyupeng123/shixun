import pygame

from settings import monster_data, BOSS_PHASE_DATA
from entity import Entity
from pathfinding_utils import astar, pos_to_grid, grid_to_pos
from resource_manager import ResourceManager


class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, obstacle_sprites, damage_player, trigger_death_particles, add_exp, trigger_exp_particles=None, pathfinding_grid=None, tile_size=None, is_boss=False, boss_phase=1, on_boss_killed=None):
        super().__init__(groups, pos)
        res = ResourceManager.instance()

        # general setup
        self.sprite_type = 'enemy'

        # graphics setup
        self.import_graphics(monster_name)
        self.status = 'idle'
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)

        # movement
        if is_boss:
            # Boss sprite is 240x240 - use smaller hitbox (64x64) to avoid
            # collision cascading across obstacle tiles
            self.hitbox = pygame.Rect(0, 0, 48, 48)
            self.hitbox.center = self.rect.center
        else:
            self.hitbox = self.rect.inflate(0, -10)
        self.obstacle_sprites = obstacle_sprites
        self.pos = pygame.math.Vector2(self.rect.center)

        # boss identity
        self.is_boss = is_boss
        self.boss_phase = boss_phase
        self.on_boss_killed = on_boss_killed

        # stats
        self.monster_name = monster_name
        monster_info = monster_data[self.monster_name]
        stat_mult = BOSS_PHASE_DATA[boss_phase]['stat_mult'] if is_boss else 1.0
        self.health = int(monster_info['health'] * stat_mult)
        self.exp = monster_info['exp']
        self.speed = monster_info['speed']  # speed not affected by boss phase
        self.attack_damage = int(monster_info['damage'] * stat_mult)
        self.resistance = monster_info['resistance']
        self.attack_radius = monster_info['attack_radius']
        self.notice_radius = monster_info['notice_radius']

        # exp orb callback
        self.trigger_exp_particles = trigger_exp_particles
        self.last_player_pos = None
        self.attack_type = monster_info['attack_type']

        # player interaction
        self.can_attack = True
        self.attack_time = None
        self.attack_cooldown = 400
        self.damage_player = damage_player
        self.trigger_death_particles = trigger_death_particles
        self.add_exp = add_exp

        # invisibility timer
        self.vulnerable = True
        self.hit_time = None
        self.invisibility_duration = 300
        self._knockback_applied = False

        # sounds (cached via ResourceManager)
        self.hit_sound = res.get_sound('../audio/hit.wav', volume=0.6)
        self.death_sound = res.get_sound('../audio/death.wav', volume=0.6)
        self.attack_sound = res.get_sound(monster_data[self.monster_name]['attack_sound'], volume=0.3)

        # Pathfinding
        self.pathfinding_grid = pathfinding_grid
        self.tile_size = tile_size
        self.path = []
        self.last_path_time = 0
        self.path_recalc_interval = 500  # ms
        self._last_player_grid = None

    # ── Asset Loading ─────────────────────────────────────────────────

    def import_graphics(self, name):
        res = ResourceManager.instance()
        self.animations = {'idle': [], 'move': [], 'attack': []}
        for animation in self.animations.keys():
            self.animations[animation] = res.get_folder_images(
                f'../graphics/monsters/{name}/' + animation)

    # ── Player Detection ──────────────────────────────────────────────

    def get_player_distance_direction(self, player):
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(player.rect.center)
        distance = (player_vec - enemy_vec).magnitude()

        if distance > 0:
            direction = (player_vec - enemy_vec).normalize()
        else:
            direction = pygame.math.Vector2()

        return (distance, direction)

    def get_status(self, player):
        distance = self.get_player_distance_direction(player)[0]

        if distance <= self.attack_radius and self.can_attack:
            if self.status != 'attack':
                self.frame_index = 0
            self.status = 'attack'
        elif distance <= self.attack_radius and not self.can_attack:
            # Stay in attack animation until cooldown finishes
            pass
        elif distance <= self.notice_radius:
            self.status = 'move'
        else:
            self.status = 'idle'
        # Clear path if not moving
        if self.status != 'move':
            self.path = []

    # ── AI Actions ────────────────────────────────────────────────────

    def actions(self, player):
        now = pygame.time.get_ticks()
        if self.status == 'attack':
            if self.can_attack:
                self.can_attack = False
                self.attack_time = now
                self.damage_player(self.attack_damage, self.attack_type)
                if self.attack_sound:
                    self.attack_sound.play()
        elif self.status == 'move':
            recalc = False
            if not self.path or now - self.last_path_time > self.path_recalc_interval:
                recalc = True
            else:
                # If player moved to a new grid cell, recalc
                current_player_grid = pos_to_grid(player.rect.center, self.tile_size)
                if self._last_player_grid != current_player_grid:
                    recalc = True
            if recalc and self.pathfinding_grid is not None:
                start = pos_to_grid(self.rect.center, self.tile_size)
                goal = pos_to_grid(player.rect.center, self.tile_size)
                self._last_player_grid = goal
                path = astar(self.pathfinding_grid, start, goal)
                if path and len(path) > 1:
                    self.path = path[1:]  # skip current position
                else:
                    self.path = []
                self.last_path_time = now
            # Follow path if available, else fallback to direct movement
            if self.path:
                next_node = self.path[0]
                next_pos = grid_to_pos(next_node, self.tile_size)
                vec_to_next = pygame.math.Vector2(next_pos) - pygame.math.Vector2(self.rect.center)
                if vec_to_next.length() < 4:  # close enough to node
                    self.path.pop(0)
                    if self.path:
                        next_node = self.path[0]
                        next_pos = grid_to_pos(next_node, self.tile_size)
                        vec_to_next = pygame.math.Vector2(next_pos) - pygame.math.Vector2(self.rect.center)
                if vec_to_next.length() > 0:
                    self.direction = vec_to_next.normalize()
                else:
                    self.direction = pygame.math.Vector2()
            else:
                # Fallback: direct movement toward player
                self.direction = self.get_player_distance_direction(player)[1]
        else:
            self.direction = pygame.math.Vector2()

    # ── Animation ─────────────────────────────────────────────────────

    def animate(self, dt):
        # Delegate frame progression to base class
        super().animate(dt)

        # boss phase color tinting
        if self.is_boss:
            phase_color = BOSS_PHASE_DATA[self.boss_phase]['color']
            if phase_color is not None:
                tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                tint.fill((*phase_color, 80))
                self.image = self.image.copy()
                self.image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        if not self.vulnerable:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    # ── Cooldowns ─────────────────────────────────────────────────────

    def cooldown(self):
        current_time = pygame.time.get_ticks()
        if not self.can_attack:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.can_attack = True

        if not self.vulnerable:
            if current_time - self.hit_time >= self.invisibility_duration:
                self.vulnerable = True
                self._knockback_applied = False

    # ── Damage ────────────────────────────────────────────────────────

    def get_damage(self, player, attack_type):
        if self.vulnerable:
            self.hit_sound.play()
            self.direction = self.get_player_distance_direction(player)[1]
            if attack_type == 'weapon':
                self.health -= player.get_full_weapon_damage()
            else:  # magic
                self.health -= player.get_full_magic_damage()
            self.hit_time = pygame.time.get_ticks()
            self.vulnerable = False

    def check_death(self):
        if self.health <= 0:
            death_pos = self.rect.center
            self.kill()
            self.trigger_death_particles(death_pos, self.monster_name)
            self.add_exp(self.exp)
            if self.trigger_exp_particles and self.last_player_pos:
                self.trigger_exp_particles(death_pos, self.last_player_pos, self.exp)
            self.death_sound.play()
            # Boss death callback
            if self.is_boss and self.on_boss_killed:
                self.on_boss_killed(death_pos)

    def hit_reaction(self):
        if not self.vulnerable:
            if not self._knockback_applied and self.direction.magnitude() > 0:
                # Apply knockback once per hit — prevents runaway direction
                # multiplication that was: direction *= -resistance every frame.
                self.direction = self.direction.normalize() * (-self.resistance)
                self._knockback_applied = True

    # ── Main Updates ──────────────────────────────────────────────────

    def update(self, dt):
        self.hit_reaction()
        self.move(self.speed, self.pos, dt)
        self.animate(dt)
        self.cooldown()
        self.check_death()

    def enemy_update(self, player):
        self.get_status(player)
        self.actions(player)
        # Store last player position for exp orb targeting
        self.last_player_pos = player.rect.center
