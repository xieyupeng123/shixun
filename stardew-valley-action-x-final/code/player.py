import pygame
from settings import weapon_data, magic_data, HITBOX_OFFSET, INVINCIBLE_SPEED_MULT, INVINCIBLE_ATTACK_MULT
from support import get_path
from entity import Entity
from resource_manager import ResourceManager
from music_state import MusicState


class Player(Entity):
    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self):
        return {
            'pos': {'x': self.pos.x, 'y': self.pos.y},
            'health': self.health,
            'energy': self.energy,
            'exp': self.exp,
            'stats': dict(self.stats),
            'max_stats': dict(self.max_stats),
            'upgrade_cost': dict(self.upgrade_cost),
            'weapon_index': self.weapon_index,
            'magic_index': self.magic_index
        }

    def from_dict(self, data):
        self.pos.x = data['pos']['x']
        self.pos.y = data['pos']['y']
        self.rect.center = (self.pos.x, self.pos.y)
        self.health = data['health']
        self.energy = data['energy']
        self.exp = data['exp']
        self.stats = dict(data['stats'])
        self.max_stats = dict(data['max_stats'])
        self.upgrade_cost = dict(data['upgrade_cost'])
        self.weapon_index = data['weapon_index']
        self.weapon = list(weapon_data.keys())[self.weapon_index]
        self.magic_index = data['magic_index']
        self.magic = list(magic_data.keys())[self.magic_index]
        # Reset invincible state on load
        self.invincible = False
        self._invincible_keys_released = True

    # ── Initialization ────────────────────────────────────────────────

    def __init__(self, pos, groups, obstacle_sprites, create_attack, destroy_attack, create_magic):
        super().__init__(groups, pos)
        res = ResourceManager.instance()

        # graphics
        self.image = res.get_image('../graphics/test/player.png')
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-6, HITBOX_OFFSET['player'])

        # animation assets
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

        # magic
        self.create_magic = create_magic
        self.magic_index = 0
        self.magic = list(magic_data.keys())[self.magic_index]
        self.can_switch_magic = True
        self.magic_switch_time = None

        # stats
        self.stats = {
            'health': 200,
            'energy': 100,
            'attack': 15,
            'magic': 5,
            'speed': 300
        }
        self.max_stats = {
            'health': 600,
            'energy': 300,
            'attack': 30,
            'magic': 15,
            'speed': 720
        }
        self.upgrade_cost = {
            'health': 100,
            'energy': 100,
            'attack': 100,
            'magic': 100,
            'speed': 100
        }
        self.health = self.stats['health']
        self.energy = self.stats['energy']
        self.speed = self.stats['speed']
        self.exp = 0

        # damage timer
        self.vulnerable = True
        self.hurt_time = None
        self.invulnerability_duration = 500

        # sound
        self.weapon_attack_sound = res.get_sound('../audio/sword.wav', volume=0.2)
        if self.weapon_attack_sound is None:
            print('[WARN] Failed to load weapon attack sound')
        self.invincible_sound = res.get_sound('../audio/invincible.ogg', volume=0.5)

        # invincible state
        self.invincible = False
        self._invincible_keys_released = True

    # ── Asset Loading ─────────────────────────────────────────────────

    def import_player_assets(self):
        res = ResourceManager.instance()
        character_path = '../graphics/player'
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
            'right_attack': [], 'left_attack': [], 'up_attack': [], 'down_attack': [],
        }

        for animation in self.animations.keys():
            full_path = character_path + '/' + animation
            self.animations[animation] = res.get_folder_images(full_path)

    # ── Input ─────────────────────────────────────────────────────────

    def input(self):
        if not self.attacking:
            keys = pygame.key.get_pressed()

            # movement
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

            # attack (mouse left button)
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:  # left click
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.create_attack()
                if self.weapon_attack_sound:
                    self.weapon_attack_sound.play()
                self.direction.x = 0
                self.direction.y = 0

            # magic (mouse right button)
            if mouse_buttons[2]:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()

                style = list(magic_data.keys())[self.magic_index]
                strength = list(magic_data.values())[
                    self.magic_index]['strength'] + self.stats['magic']
                cost = list(magic_data.values())[self.magic_index]['cost']
                self.create_magic(style, strength, cost)
                self.direction.x = 0
                self.direction.y = 0

            if keys[pygame.K_q] and self.can_switch_weapon:
                self.can_switch_weapon = False
                self.weapon_switch_time = pygame.time.get_ticks()

                if self.weapon_index < len(list(weapon_data.keys()))-1:
                    self.weapon_index += 1
                else:
                    self.weapon_index = 0

                self.weapon = list(weapon_data.keys())[self.weapon_index]

            if keys[pygame.K_e] and self.can_switch_magic:
                self.can_switch_magic = False
                self.magic_switch_time = pygame.time.get_ticks()

                if self.magic_index < len(list(magic_data.keys()))-1:
                    self.magic_index += 1
                else:
                    self.magic_index = 0

                self.magic = list(magic_data.keys())[self.magic_index]

            # invincible toggle: SPACE key
            if keys[pygame.K_SPACE]:
                if self._invincible_keys_released:
                    self._invincible_keys_released = False
                    self.invincible = not self.invincible
                    if self.invincible:
                        # Stop current BGM, play invincible sound (looping)
                        pygame.mixer.music.stop()
                        if self.invincible_sound:
                            self.invincible_sound.play(-1)
                    else:
                        # Stop invincible sound, restore current BGM
                        if self.invincible_sound:
                            self.invincible_sound.stop()
                        if MusicState.get() == 1:
                            bgm_path = get_path('../audio/boss_bgm.ogg')
                            vol = 0.5
                        else:
                            bgm_path = get_path('../audio/game_bgm.ogg')
                            vol = 0.3
                        pygame.mixer.music.load(bgm_path)
                        pygame.mixer.music.set_volume(vol)
                        pygame.mixer.music.play(-1)
            else:
                self._invincible_keys_released = True

    # ── Status ────────────────────────────────────────────────────────

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

    # ── Cooldowns ─────────────────────────────────────────────────────

    def cooldowns(self):
        current_time = pygame.time.get_ticks()

        if self.attacking:
            if current_time - self.attack_time >= self.attack_cooldown + weapon_data[self.weapon]['cooldown']:
                self.attacking = False
                self.destroy_attack()

        if not self.can_switch_weapon:
            if current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
                self.can_switch_weapon = True

        if not self.can_switch_magic:
            if current_time - self.magic_switch_time >= self.switch_duration_cooldown:
                self.can_switch_magic = True

        if not self.vulnerable:
            if current_time - self.hurt_time >= self.invulnerability_duration:
                self.vulnerable = True

    # ── Animation ─────────────────────────────────────────────────────

    def animate(self, dt):
        # Delegate frame progression to base class
        super().animate(dt)

        # Reposition rect around hitbox
        self.rect = self.image.get_rect(center=self.hitbox.center)

        # flicker when hurt
        if not self.vulnerable:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

        # golden tint for invincible state
        if self.invincible:
            gold_overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            gold_overlay.fill((255, 200, 0, 80))
            self.image = self.image.copy()
            self.image.blit(gold_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # ── Damage Calculation ────────────────────────────────────────────

    def get_full_weapon_damage(self):
        base_damage = self.stats['attack']
        weapon_damage = weapon_data[self.weapon]['damage']
        damage = base_damage + weapon_damage
        if self.invincible:
            damage *= INVINCIBLE_ATTACK_MULT
        return damage

    def get_full_magic_damage(self):
        base_damage = self.stats['magic']
        spell_damage = magic_data[self.magic]['strength']
        damage = base_damage + spell_damage
        if self.invincible:
            damage *= INVINCIBLE_ATTACK_MULT
        return damage

    # ── Upgrade Helpers ───────────────────────────────────────────────

    def get_value_by_index(self, idx):
        return list(self.stats.values())[idx]

    def get_cost_by_index(self, idx):
        return list(self.upgrade_cost.values())[idx]

    # ── Weapon Cycling ────────────────────────────────────────────────

    def cycle_weapon(self, direction):
        """Switch weapon with mouse wheel. direction > 0 = next, < 0 = previous."""
        if not self.can_switch_weapon:
            return
        self.can_switch_weapon = False
        self.weapon_switch_time = pygame.time.get_ticks()
        weapon_keys = list(weapon_data.keys())
        if direction > 0:
            self.weapon_index = (self.weapon_index + 1) % len(weapon_keys)
        else:
            self.weapon_index = (self.weapon_index - 1) % len(weapon_keys)
        self.weapon = weapon_keys[self.weapon_index]

    # ── Energy Recovery ───────────────────────────────────────────────

    def energy_recovery(self, dt):
        if self.energy < self.stats['energy']:
            self.energy += self.stats['magic'] * dt
        else:
            self.energy = self.stats['energy']

    # ── Main Update ───────────────────────────────────────────────────

    def update(self, dt):
        self.input()
        self.cooldowns()
        self.get_status()
        self.animate(dt)
        # Apply invincible speed multiplier
        speed = self.stats['speed']
        if self.invincible:
            speed *= INVINCIBLE_SPEED_MULT
        self.move(speed, self.pos, dt)
        self.energy_recovery(dt)
