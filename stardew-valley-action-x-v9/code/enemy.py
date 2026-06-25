import pygame
from settings import monster_data, BOSS_PHASE_THRESHOLDS, BOSS_PHASE_COLORS
from entity import Entity
from combat import calculate_damage
from support import import_folder
from pathfinding_utils import astar, pos_to_grid, grid_to_pos


class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, obstacle_sprites,
                 damage_player, trigger_death_particles, add_exp,
                 trigger_exp_particles=None, on_boss_killed=None,
                 pathfinding_grid=None):
        super().__init__(groups, pos)
        self.sprite_type = 'enemy'

        self.monster_name = monster_name
        self.is_boss = (monster_name == 'boss')
        info = monster_data[self.monster_name]
        self.max_health = info['health']
        self.health = self.max_health
        self.speed = info['speed']
        self.attack_damage = info['damage']
        self.resistance = info['resistance']
        self.attack_radius = info['attack_radius']
        self.notice_radius = info['notice_radius']
        self.exp = info['exp']

        self.import_graphics(monster_name)
        self.status = 'idle'
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-20, -20) if self.is_boss \
            else self.rect.inflate(0, -10)
        self.obstacle_sprites = obstacle_sprites
        self.pos = pygame.math.Vector2(self.rect.center)

        self.can_attack = True
        self.attack_time = None
        self.attack_cooldown = 400
        self.damage_player = damage_player
        self.trigger_death_particles = trigger_death_particles
        self.add_exp = add_exp
        self.trigger_exp_particles = trigger_exp_particles
        self.on_boss_killed = on_boss_killed

        self.vulnerable = True
        self.hit_time = None
        self.invisibility_duration = 300

        self.pathfinding_grid = pathfinding_grid
        self.tile_size = 64
        self.path = []
        self.last_path_time = 0
        self.path_recalc_interval = 500
        self._last_player_grid = None

        self._current_phase = 0
        self._knockback_applied = False
        self.last_player_pos = None

    def import_graphics(self, name):
        sprite_name = 'squid' if name == 'boss' else name
        self.animations = {'idle': [], 'move': [], 'attack': []}
        for anim in self.animations.keys():
            self.animations[anim] = import_folder(
                f'../graphics/monsters/{sprite_name}/' + anim)

    def get_player_distance_direction(self, player):
        ev = pygame.math.Vector2(self.rect.center)
        pv = pygame.math.Vector2(player.rect.center)
        d = (pv - ev).length()
        return d, (pv - ev).normalize() if d > 0 else pygame.math.Vector2()

    def get_status(self, player):
        d = self.get_player_distance_direction(player)[0]
        if d <= self.attack_radius and self.can_attack:
            if self.status != 'attack':
                self.frame_index = 0
            self.status = 'attack'
        elif d <= self.notice_radius:
            self.status = 'move'
        else:
            self.status = 'idle'
        if self.status != 'move':
            self.path = []

    def actions(self, player):
        now = pygame.time.get_ticks()
        if self.status == 'attack':
            self.attack_time = now
            dmg = self.attack_damage
            if self.is_boss and self._current_phase >= 1:
                dmg = int(dmg * (1 + 0.5 * self._current_phase))
            self.damage_player(dmg, self.monster_name)
            self.can_attack = False
        elif self.status == 'move':
            recalc = False
            if not self.path or now - self.last_path_time > self.path_recalc_interval:
                recalc = True
            else:
                cur = pos_to_grid(player.rect.center, self.tile_size)
                if self._last_player_grid != cur:
                    recalc = True
            if recalc and self.pathfinding_grid is not None:
                s = pos_to_grid(self.rect.center, self.tile_size)
                g = pos_to_grid(player.rect.center, self.tile_size)
                self._last_player_grid = g
                path = astar(self.pathfinding_grid, s, g)
                self.path = path[1:] if path and len(path) > 1 else []
                self.last_path_time = now
            if self.path:
                n = self.path[0]
                np = grid_to_pos(n, self.tile_size)
                v = pygame.math.Vector2(np) - \
                    pygame.math.Vector2(self.rect.center)
                if v.length() < 4:
                    self.path.pop(0)
                    if self.path:
                        np = grid_to_pos(self.path[0], self.tile_size)
                        v = pygame.math.Vector2(np) - \
                            pygame.math.Vector2(self.rect.center)
                self.direction = v.normalize() if v.length() > 0 \
                    else pygame.math.Vector2()
            else:
                self.direction = self.get_player_distance_direction(player)[1]
        else:
            self.direction = pygame.math.Vector2()

    def get_damage(self, amount):
        if self.vulnerable:
            self.health -= calculate_damage(amount, self.resistance)
            self.vulnerable = False
            self.hit_time = pygame.time.get_ticks()
            self._knockback_applied = False
            if self.is_boss:
                self._check_phase()

    def _check_phase(self):
        hp_ratio = self.health / self.max_health
        for i, thresh in enumerate(BOSS_PHASE_THRESHOLDS):
            if hp_ratio <= thresh and self._current_phase <= i:
                self._current_phase = i + 1
                self.speed = int(self.speed * 1.2)

    def check_death(self):
        if self.health <= 0:
            death_pos = self.rect.center
            self.kill()
            if self.trigger_exp_particles and self.last_player_pos:
                self.trigger_exp_particles(
                    death_pos, self.last_player_pos, self.exp)
            if self.trigger_death_particles:
                name = 'squid' if self.monster_name == 'boss' \
                    else self.monster_name
                self.trigger_death_particles(death_pos, name)
            if self.on_boss_killed:
                self.on_boss_killed(death_pos)
            self.add_exp(self.exp)

    def animate(self, dt):
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(animation):
            if self.status == 'attack':
                self.can_attack = False
            self.frame_index = 0
        self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center=self.hitbox.center)

        if self.is_boss and self._current_phase >= 1:
            tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            tint.fill(BOSS_PHASE_COLORS[self._current_phase] + (80,))
            self.image = self.image.copy()
            self.image.blit(tint, (0, 0))
        self.image.set_alpha(
            self.wave_value() if not self.vulnerable else 255)

    def cooldowns(self):
        now = pygame.time.get_ticks()
        if not self.can_attack:
            if now - self.attack_time >= self.attack_cooldown:
                self.can_attack = True
        if not self.vulnerable:
            if now - self.hit_time >= self.invisibility_duration:
                self.vulnerable = True

    def hit_reaction(self):
        if not self.vulnerable and not self._knockback_applied:
            self._knockback_applied = True
            self.direction *= -self.resistance

    def update(self, dt):
        self.hit_reaction()
        self.move(self.speed, self.pos, dt)
        self.animate(dt)
        self.cooldowns()
        self.check_death()

    def enemy_update(self, player):
        self.last_player_pos = player.rect.center
        self.get_status(player)
        self.actions(player)
