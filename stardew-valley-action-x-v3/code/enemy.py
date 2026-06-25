import pygame
from settings import monster_data
from entity import Entity
from combat import calculate_damage


class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, obstacle_sprites,
                 damage_player, add_exp):
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

        # graphics — simple colored blob
        size = 44 if monster_name == 'slime' else 56
        self.image = pygame.Surface((size, size))
        self.draw_enemy_sprite(monster_name, size)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.obstacle_sprites = obstacle_sprites

        # AI state
        self.status = 'idle'
        self.status_colors = {
            'idle': (100, 180, 100),   # calm green
            'move': (255, 200, 50),     # alert yellow
            'attack': (255, 60, 60),    # angry red
        }

        # combat
        self.can_attack = True
        self.attack_time = None
        self.attack_cooldown = 600
        self.damage_player = damage_player
        self.add_exp = add_exp

        # hurt flash
        self.vulnerable = True
        self.hit_time = None
        self.invisibility_duration = 200

    def draw_enemy_sprite(self, name, size):
        """Draw a simple enemy sprite programmatically."""
        color = (100, 200, 100) if name == 'slime' else (200, 120, 80)
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        # Body — filled circle
        pygame.draw.ellipse(self.image, color,
                            (2, size // 4, size - 4, size // 2))
        # Eyes
        eye_color = (255, 255, 255)
        pupil_color = (20, 20, 20)
        pygame.draw.circle(self.image, eye_color, (size // 3, size // 3 - 2), 5)
        pygame.draw.circle(self.image, eye_color,
                           (2 * size // 3, size // 3 - 2), 5)
        pygame.draw.circle(self.image, pupil_color,
                           (size // 3, size // 3 - 2), 2)
        pygame.draw.circle(self.image, pupil_color,
                           (2 * size // 3, size // 3 - 2), 2)

    def get_player_distance_direction(self, player):
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(player.rect.center)
        distance = (player_vec - enemy_vec).length()
        direction = (player_vec - enemy_vec).normalize() if distance > 0 \
            else pygame.math.Vector2()
        return distance, direction

    def get_status(self, player):
        distance = self.get_player_distance_direction(player)[0]
        if distance <= self.attack_radius and self.can_attack:
            self.status = 'attack'
        elif distance <= self.notice_radius:
            self.status = 'move'
        else:
            self.status = 'idle'

    def actions(self, player):
        now = pygame.time.get_ticks()
        if self.status == 'attack':
            self.attack_time = now
            self.damage_player(self.attack_damage)
            self.can_attack = False
        elif self.status == 'move':
            _, self.direction = self.get_player_distance_direction(player)
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

    def update_status_color(self):
        """Update sprite color based on AI state."""
        color = self.status_colors.get(self.status, (100, 180, 100))
        self.draw_enemy_sprite(self.monster_name, self.image.get_width())
        # Tint with current status color
        tint = pygame.Surface(self.image.get_size())
        tint.fill(color)
        tint.set_colorkey((0, 0, 0))
        tint.set_alpha(80)
        self.image.blit(tint, (0, 0))

    def cooldowns(self):
        current_time = pygame.time.get_ticks()
        if not self.can_attack:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.can_attack = True
        if not self.vulnerable:
            if current_time - self.hit_time >= self.invisibility_duration:
                self.vulnerable = True

    def update(self, dt):
        self.cooldowns()
        self.move(self.speed, self.pos, dt)
        self.check_death()

    def enemy_update(self, player):
        self.get_status(player)
        self.actions(player)
