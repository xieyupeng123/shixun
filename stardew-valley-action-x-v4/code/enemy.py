import pygame
from settings import monster_data
from entity import Entity
from combat import calculate_damage
from pathfinding_utils import astar, pos_to_grid, grid_to_pos


class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, obstacle_sprites,
                 damage_player, add_exp, pathfinding_grid=None):
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

        # graphics
        size = 44
        self.image = pygame.Surface((size, size))
        self._draw_sprite(size)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.obstacle_sprites = obstacle_sprites

        # AI
        self.status = 'idle'
        self.status_colors = {
            'idle': (100, 180, 100), 'move': (255, 200, 50), 'attack': (255, 60, 60)}

        # combat
        self.can_attack = True
        self.attack_time = None
        self.attack_cooldown = 600
        self.damage_player = damage_player
        self.add_exp = add_exp

        # hurt
        self.vulnerable = True
        self.hit_time = None
        self.invisibility_duration = 200

        # A* pathfinding
        self.pathfinding_grid = pathfinding_grid
        self.tile_size = 64
        self.path = []
        self.last_path_time = 0
        self.path_recalc_interval = 500
        self._last_player_grid = None

    def _draw_sprite(self, size):
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.ellipse(self.image, (100, 200, 100),
                            (2, size // 4, size - 4, size // 2))
        pygame.draw.circle(self.image, (255, 255, 255), (size // 3, size // 3 - 2), 5)
        pygame.draw.circle(self.image, (255, 255, 255),
                           (2 * size // 3, size // 3 - 2), 5)
        pygame.draw.circle(self.image, (20, 20, 20), (size // 3, size // 3 - 2), 2)
        pygame.draw.circle(self.image, (20, 20, 20),
                           (2 * size // 3, size // 3 - 2), 2)

    def get_player_distance_direction(self, player):
        ev = pygame.math.Vector2(self.rect.center)
        pv = pygame.math.Vector2(player.rect.center)
        distance = (pv - ev).length()
        direction = (pv - ev).normalize() if distance > 0 else pygame.math.Vector2()
        return distance, direction

    def get_status(self, player):
        distance = self.get_player_distance_direction(player)[0]
        if distance <= self.attack_radius and self.can_attack:
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
            self.add_exp(self.exp)
            self.kill()

    def cooldowns(self):
        now = pygame.time.get_ticks()
        if not self.can_attack:
            if now - self.attack_time >= self.attack_cooldown:
                self.can_attack = True
        if not self.vulnerable:
            if now - self.hit_time >= self.invisibility_duration:
                self.vulnerable = True

    def update(self, dt):
        self.cooldowns()
        self.move(self.speed, self.pos, dt)
        self.check_death()

    def enemy_update(self, player):
        self.get_status(player)
        self.actions(player)
