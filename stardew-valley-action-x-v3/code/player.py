import pygame
from settings import HITBOX_OFFSET
from support import get_path, import_folder
from entity import Entity


class Player(Entity):
    def __init__(self, pos, groups, obstacle_sprites, create_attack, destroy_attack):
        super().__init__(groups, pos)
        player_path = get_path('../graphics/test/player.png')
        self.image = pygame.image.load(player_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-6, HITBOX_OFFSET['player'])

        # graphics
        self.import_player_assets()
        self.status = 'down'

        # movement
        self.pos = pygame.math.Vector2(self.rect.center)
        self.obstacle_sprites = obstacle_sprites
        self.speed = 300

        # attack
        self.attacking = False
        self.attack_cooldown = 400
        self.attack_time = None
        self.create_attack = create_attack
        self.destroy_attack = destroy_attack
        self.attack_damage = 20

        # stats
        self.health = 200
        self.max_health = 200
        self.exp = 0

        # hurt
        self.vulnerable = True
        self.hurt_time = None
        self.invulnerability_duration = 500

    def import_player_assets(self):
        character_path = get_path('../graphics/player')
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': [],
            'up_attack': [], 'down_attack': [],
            'left_attack': [], 'right_attack': [],
        }

        for animation in self.animations.keys():
            full_path = character_path + '/' + animation
            self.animations[animation] = import_folder(full_path)

    def input(self):
        if not self.attacking:
            keys = pygame.key.get_pressed()

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.direction.x = 1
                self.status = 'right'
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.direction.x = -1
                self.status = 'left'
            else:
                self.direction.x = 0

            if keys[pygame.K_SPACE]:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.create_attack()
                self.direction.x = 0
                self.direction.y = 0

    def get_status(self):
        if self.direction.x == 0 and self.direction.y == 0:
            if 'idle' not in self.status and 'attack' not in self.status:
                self.status = self.status + '_idle'

            if self.attacking:
                self.direction.x = 0
                self.direction.y = 0
                if 'attack' not in self.status:
                    if 'idle' in self.status:
                        self.status = self.status.replace('_idle', '_attack')
                    else:
                        self.status = self.status + '_attack'
            else:
                if 'attack' in self.status:
                    self.status = self.status.replace('_attack', '')
        else:
            if '_idle' in self.status:
                self.status = self.status.replace('_idle', '')

    def cooldowns(self):
        current_time = pygame.time.get_ticks()
        if self.attacking:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.attacking = False
                self.destroy_attack()
        if not self.vulnerable:
            if current_time - self.hurt_time >= self.invulnerability_duration:
                self.vulnerable = True

    def take_damage(self, amount):
        if self.vulnerable:
            self.health -= amount
            self.vulnerable = False
            self.hurt_time = pygame.time.get_ticks()

    def add_exp(self, amount):
        self.exp += amount

    def animate(self, dt):
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(animation):
            self.frame_index = 0
        self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center=self.hitbox.center)

        # flicker when hurt
        if not self.vulnerable:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def update(self, dt):
        self.input()
        self.cooldowns()
        self.get_status()
        self.animate(dt)
        self.move(self.speed, self.pos, dt)
