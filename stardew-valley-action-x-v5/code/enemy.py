import pygame
from settings import monster_data
from entity import Entity
from combat import calculate_damage
from support import import_folder, get_path
from pathfinding_utils import astar, pos_to_grid, grid_to_pos


class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, obstacle_sprites,
                 damage_player, add_exp, trigger_death_particles=None,
                 pathfinding_grid=None):
        super().__init__(groups, pos)
        self.sprite_type = 'enemy'

        # stats
        self.monster_name = monster_name
        info = monster_data[self.monster_name]
        self.health = info['health']
        self.speed = info['speed']
        self.attack_damage = info['damage']
        self.resistance = info['resistance']
        self.attack_radius = info['attack_radius']
        self.notice_radius = info['notice_radius']
        self.exp = info['exp']

        # graphics — real sprite animations
        self.import_graphics(monster_name)
        self.status = 'idle'
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)

        # movement
        self.hitbox = self.rect.inflate(0, -10)
        self.obstacle_sprites = obstacle_sprites
        self.pos = pygame.math.Vector2(self.rect.center)

        # combat
        self.can_attack = True
        self.attack_time = None
        self.attack_cooldown = 400
        self.damage_player = damage_player
        self.add_exp = add_exp
        self.trigger_death_particles = trigger_death_particles

        # hurt
        self.vulnerable = True
        self.hit_time = None
        self.invisibility_duration = 300

        # A* pathfinding
        self.pathfinding_grid = pathfinding_grid
        self.tile_size = 64
        self.path = []
        self.last_path_time = 0
        self.path_recalc_interval = 500
        self._last_player_grid = None

    def import_graphics(self, name):
        self.animations = {'idle': [], 'move': [], 'attack': []}
        for animation in self.animations.keys():
            self.animations[animation] = import_folder(
                f'../graphics/monsters/{name}/' + animation)

    def get_player_distance_direction(self, player):
        ev = pygame.math.Vector2(self.rect.center)
        pv = pygame.math.Vector2(player.rect.center)
        distance = (pv - ev).length()
        direction = (pv - ev).normalize() if distance > 0 else pygame.math.Vector2()
        return distance, direction

    def get_status(self, player):
        distance = self.get_player_distance_direction(player)[0]
        if distance <= self.attack_radius and self.can_attack:
            if self.status != 'attack':
                self.frame_index = 0
            self.status = 'attack'
        elif distance <= self.notice_radius:
            self.status = 'move'
        else:
            self.status = 'idle'
        if self.status != 'move':
            self.path = []

    def actions(self, player):
        now = pygame.time.get_ticks()
        if self.status == 'attack':
            self.attack_time = now
            self.damage_player(self.attack_damage)
            self.can_attack = False
        elif self.status == 'move':
            recalc = False
            if not self.path or now - self.last_path_time > self.path_recalc_interval:
                recalc = True
            else:
                cur_grid = pos_to_grid(player.rect.center, self.tile_size)
                if self._last_player_grid != cur_grid:
                    recalc = True
            if recalc and self.pathfinding_grid is not None:
                start = pos_to_grid(self.rect.center, self.tile_size)
                goal = pos_to_grid(player.rect.center, self.tile_size)
                self._last_player_grid = goal
                path = astar(self.pathfinding_grid, start, goal)
                self.path = path[1:] if path and len(path) > 1 else []
                self.last_path_time = now
            if self.path:
                next_node = self.path[0]
                next_pos = grid_to_pos(next_node, self.tile_size)
                vec = pygame.math.Vector2(next_pos) - pygame.math.Vector2(self.rect.center)
                if vec.length() < 4:
                    self.path.pop(0)
                    if self.path:
                        next_pos = grid_to_pos(self.path[0], self.tile_size)
                        vec = pygame.math.Vector2(next_pos) - pygame.math.Vector2(self.rect.center)
                self.direction = vec.normalize() if vec.length() > 0 else pygame.math.Vector2()
            else:
                self.direction = self.get_player_distance_direction(player)[1]
        else:
            self.direction = pygame.math.Vector2()

    def get_damage(self, amount):
        if self.vulnerable:
            self.health -= calculate_damage(amount, self.resistance)
            self.vulnerable = False
            self.hit_time = pygame.time.get_ticks()

    def check_death(self):
        if self.health <= 0:
            self.kill()
            if self.trigger_death_particles:
                self.trigger_death_particles(
                    self.rect.center, self.monster_name)
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

        if not self.vulnerable:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def cooldowns(self):
        now = pygame.time.get_ticks()
        if not self.can_attack:
            if now - self.attack_time >= self.attack_cooldown:
                self.can_attack = True
        if not self.vulnerable:
            if now - self.hit_time >= self.invisibility_duration:
                self.vulnerable = True

    def hit_reaction(self):
        if not self.vulnerable:
            self.direction *= -self.resistance

    def update(self, dt):
        self.hit_reaction()
        self.move(self.speed, self.pos, dt)
        self.animate(dt)
        self.cooldowns()
        self.check_death()

    def enemy_update(self, player):
        self.get_status(player)
        self.actions(player)
