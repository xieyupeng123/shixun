import pygame
from settings import weapon_data, magic_data, HITBOX_OFFSET
from support import get_path, import_folder
from entity import Entity


class Player(Entity):
    def __init__(self, pos, groups, obstacle_sprites,
                 create_attack, destroy_attack, create_magic):
        super().__init__(groups, pos)

        self.image = pygame.image.load(
            get_path('../graphics/test/player.png')).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-6, HITBOX_OFFSET['player'])

        self.import_player_assets()
        self.status = 'down'

        # movement
        self.attacking = False
        self.attack_cooldown = 400
        self.attack_time = None
        self.pos = pygame.math.Vector2(self.rect.center)
        self.obstacle_sprites = obstacle_sprites

        # weapon
        self.create_attack = create_attack
        self.destroy_attack = destroy_attack
        self.weapon_index = 0
        self.weapon = list(weapon_data.keys())[self.weapon_index]
        self.can_switch_weapon = True
        self.weapon_switch_time = None
        self.switch_duration_cooldown = 200
        self.attack_damage = 20

        # magic
        self.create_magic = create_magic
        self.magic_index = 0
        self.magic = list(magic_data.keys())[self.magic_index]
        self.can_switch_magic = True
        self.magic_switch_time = None

        # stats
        self.health = 200
        self.max_health = 200
        self.energy = 100
        self.max_energy = 100
        self.speed = 300
        self.exp = 0

        # upgrade levels
        self.upgrade_levels = {
            'health': 0, 'energy': 0, 'attack': 0, 'magic': 0, 'speed': 0}

        # damage timer
        self.vulnerable = True
        self.hurt_time = None
        self.invulnerability_duration = 500

    def upgrade_cost(self, name):
        base = {'health': 100, 'energy': 100, 'attack': 80, 'magic': 120, 'speed': 60}
        return base[name] + self.upgrade_levels[name] * 50

    def to_dict(self):
        return {
            'pos': {'x': self.pos.x, 'y': self.pos.y},
            'health': self.health, 'max_health': self.max_health,
            'energy': self.energy, 'max_energy': self.max_energy,
            'exp': self.exp, 'attack_damage': self.attack_damage,
            'speed': self.speed, 'upgrade_levels': dict(self.upgrade_levels),
            'weapon_index': self.weapon_index,
            'magic_index': self.magic_index,
        }

    def from_dict(self, data):
        self.pos.x = data['pos']['x']
        self.pos.y = data['pos']['y']
        self.rect.center = (self.pos.x, self.pos.y)
        self.health = data['health']
        self.max_health = data.get('max_health', 200)
        self.energy = data.get('energy', 100)
        self.max_energy = data.get('max_energy', 100)
        self.exp = data['exp']
        self.attack_damage = data.get('attack_damage', 20)
        self.speed = data.get('speed', 300)
        self.upgrade_levels = data.get('upgrade_levels', {
            'health': 0, 'energy': 0, 'attack': 0, 'magic': 0, 'speed': 0})
        self.weapon_index = data['weapon_index']
        self.weapon = list(weapon_data.keys())[self.weapon_index]
        self.magic_index = data.get('magic_index', 0)
        self.magic = list(magic_data.keys())[self.magic_index]

    def import_player_assets(self):
        character_path = get_path('../graphics/player')
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
            'right_attack': [], 'left_attack': [],
            'up_attack': [], 'down_attack': [],
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

            mouse_buttons = pygame.mouse.get_pressed()
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.create_attack()
                self.direction.x = 0
                self.direction.y = 0

            if mouse_buttons[2] or keys[pygame.K_LCTRL]:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                style = list(magic_data.keys())[self.magic_index]
                strength = magic_data[style]['strength']
                cost = magic_data[style]['cost']
                self.create_magic(style, strength, cost)
                self.direction.x = 0
                self.direction.y = 0

            if keys[pygame.K_q] and self.can_switch_weapon:
                self.can_switch_weapon = False
                self.weapon_switch_time = pygame.time.get_ticks()
                if self.weapon_index < len(list(weapon_data.keys())) - 1:
                    self.weapon_index += 1
                else:
                    self.weapon_index = 0
                self.weapon = list(weapon_data.keys())[self.weapon_index]

            if keys[pygame.K_e] and self.can_switch_magic:
                self.can_switch_magic = False
                self.magic_switch_time = pygame.time.get_ticks()
                if self.magic_index < len(list(magic_data.keys())) - 1:
                    self.magic_index += 1
                else:
                    self.magic_index = 0
                self.magic = list(magic_data.keys())[self.magic_index]

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

    def cooldowns(self):
        now = pygame.time.get_ticks()
        if self.attacking:
            if now - self.attack_time >= self.attack_cooldown + weapon_data[self.weapon]['cooldown']:
                self.attacking = False
                self.destroy_attack()
        if not self.can_switch_weapon:
            if now - self.weapon_switch_time >= self.switch_duration_cooldown:
                self.can_switch_weapon = True
        if not self.can_switch_magic:
            if now - self.magic_switch_time >= self.switch_duration_cooldown:
                self.can_switch_magic = True
        if not self.vulnerable:
            if now - self.hurt_time >= self.invulnerability_duration:
                self.vulnerable = True

    def energy_recovery(self, dt):
        if self.energy < self.max_energy:
            self.energy += 5 * dt
            if self.energy > self.max_energy:
                self.energy = self.max_energy

    def animate(self, dt):
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(animation):
            self.frame_index = 0
        self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center=self.hitbox.center)
        self.image.set_alpha(self.wave_value() if not self.vulnerable else 255)

    def take_damage(self, amount):
        if self.vulnerable:
            self.health -= amount
            self.vulnerable = False
            self.hurt_time = pygame.time.get_ticks()

    def add_exp(self, amount):
        self.exp += amount

    def cycle_weapon(self, direction):
        if not self.can_switch_weapon:
            return
        self.can_switch_weapon = False
        self.weapon_switch_time = pygame.time.get_ticks()
        keys = list(weapon_data.keys())
        self.weapon_index = ((self.weapon_index + (1 if direction > 0 else -1))
                             % len(keys))
        self.weapon = keys[self.weapon_index]

    def update(self, dt):
        self.input()
        self.cooldowns()
        self.get_status()
        self.animate(dt)
        self.move(self.speed, self.pos, dt)
        self.energy_recovery(dt)
