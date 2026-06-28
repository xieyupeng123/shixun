"""
player —— 玩家角色类模块

本模块定义了 Player 类，继承自 Entity 基类，是游戏中玩家操控的角色。
负责处理：
  - 键盘/鼠标输入（移动、攻击、魔法、武器切换、无敌模式触发）
  - 动画状态机（idle/attack 切换、方向跟踪）
  - 冷却管理（攻击冷却、武器/魔法切换冷却、受击无敌冷却）
  - 属性系统（生命、能量、攻击力、魔法、速度及升级）
  - 无敌模式（invincible）的激活/过期/冷却/代价逻辑
  - 玩家数据的序列化与反序列化（存档/读档）
"""

import pygame
from settings import weapon_data, magic_data, HITBOX_OFFSET, INVINCIBLE_SPEED_MULT, INVINCIBLE_ATTACK_MULT, INVINCIBLE_DURATION, INVINCIBLE_COOLDOWN, INVINCIBLE_COST_HEALTH, INVINCIBLE_COST_ENERGY
from support import get_path
from entity import Entity
from resource_manager import ResourceManager
from music_state import MusicState


class Player(Entity):
    """Player —— 玩家角色类

    继承自 Entity，在基类移动/碰撞/动画基础上增加：
      - 输入处理（键盘 WASD/方向键 + 鼠标左右键 + Q/E/空格键）
      - 武器与魔法系统（切换、攻击创建与销毁）
      - 属性数值及升级机制
      - 无敌模式：限时爆发 + 冷却 + 代价惩罚
      - 受击无敌（短暂闪烁无敌）与全局无敌（独立系统）
      - 存档序列化（to_dict / from_dict）

    状态机说明:
      方向状态:  up / down / left / right
      空闲后缀:  + '_idle'（静止时自动添加）
      攻击后缀:  + '_attack'（攻击动画期间）
      示例:     'down' -> 'down_idle' -> 'down_attack' -> 'down'
    """

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self):
        """将玩家当前状态序列化为字典（用于存档保存）

        保存的数据包括：位置、生命值、能量、经验、各属性值、
        各属性上限、升级消耗、当前武器/魔法索引。
        不保存无敌状态（读档时重置为 False，避免存档作弊）。

        返回:
            dict: 包含上述所有字段的字典，可直接用于存档 JSON 序列化
        """
        return {
            'pos': {'x': self.pos.x, 'y': self.pos.y},  # 玩家中心坐标（像素）
            'health': self.health,       # 当前生命值
            'energy': self.energy,       # 当前能量值
            'exp': self.exp,             # 当前经验值
            'stats': dict(self.stats),   # 当前五维属性（副本，防外部修改）
            'max_stats': dict(self.max_stats),   # 属性上限
            'upgrade_cost': dict(self.upgrade_cost),  # 各属性升级所需经验
            'weapon_index': self.weapon_index,     # 当前武器在 weapon_data 中的索引
            'magic_index': self.magic_index        # 当前魔法在 magic_data 中的索引
        }

    def from_dict(self, data):
        """从字典中恢复玩家状态（用于读档加载）

        从 data 中逐个读取 to_dict 保存的字段，恢复玩家到存档时的状态。
        不恢复无敌相关状态（self.invincible = False 确保读档后不会有残留无敌）。

        参数:
            data (dict): 由 to_dict() 生成的玩家数据字典
        """
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
        # 根据索引从配置数据中获取武器名称字符串
        self.weapon = list(weapon_data.keys())[self.weapon_index]
        self.magic_index = data['magic_index']
        self.magic = list(magic_data.keys())[self.magic_index]

        # ── 读档时重置无敌状态 ──
        # 防止存档文件中残留的无敌数据被恢复（防作弊）
        self.invincible = False
        self.invincible_start_time = None
        self.invincible_cooldown_until = 0
        self._invincible_keys_released = True

    # ── Initialization ────────────────────────────────────────────────

    def __init__(self, pos, groups, obstacle_sprites, create_attack, destroy_attack, create_magic):
        """初始化玩家对象

        参数:
            pos (tuple[int, int]): 出生坐标 (x, y)，单位为像素
            groups (list[pygame.sprite.Group]): 要加入的精灵组列表
            obstacle_sprites (pygame.sprite.Group): 障碍物精灵组，用于碰撞检测
            create_attack (callable): 创建武器攻击精灵的回调函数（由上层注入）
            destroy_attack (callable): 销毁武器攻击精灵的回调函数
            create_magic (callable): 创建魔法攻击精灵的回调函数
        """
        super().__init__(groups, pos)
        res = ResourceManager.instance()

        # ── 图形与碰撞箱 ──
        # 加载初始玩家图片（默认占位图，动画系统启动后会立刻替换）
        self.image = res.get_image('../graphics/test/player.png')
        # 以 pos 为左上角创建矩形区域
        self.rect = self.image.get_rect(topleft=pos)
        # hitbox 比 rect 略小，使碰撞判定更宽松、手感更好
        # inflate(-6, ...) 使 hitbox 在 X 方向缩小 6 像素
        # HITBOX_OFFSET['player'] 是配置文件中玩家 hitbox 的 Y 方向偏移量
        self.hitbox = self.rect.inflate(-6, HITBOX_OFFSET['player'])

        # ── 动画资源 ──
        self.import_player_assets()
        # 初始朝向：向下
        self.status = 'down'

        # ── 移动相关 ──
        self.attacking = False        # 是否正在攻击（攻击动画期间为 True）
        self.attack_cooldown = 400    # 攻击基础冷却时间（毫秒）
        self.attack_time = None       # 上次攻击的时间戳（毫秒）
        # 位置向量（以矩形中心为基准，用于精确移动计算）
        self.pos = pygame.math.Vector2(self.rect.center)

        self.obstacle_sprites = obstacle_sprites  # 障碍物精灵组引用

        # ── 武器系统 ──
        self.create_attack = create_attack   # 创建攻击精灵的回调
        self.destroy_attack = destroy_attack # 销毁攻击精灵的回调
        self.weapon_index = 0                # 当前武器索引（默认第一把）
        self.weapon = list(weapon_data.keys())[self.weapon_index]  # 武器名称
        self.can_switch_weapon = True        # 是否可以切换武器（冷却中为 False）
        self.weapon_switch_time = None       # 上次切换武器的时间戳
        self.switch_duration_cooldown = 200  # 切换武器冷却时间（毫秒）

        # ── 魔法系统 ──
        self.create_magic = create_magic     # 创建魔法精灵的回调
        self.magic_index = 0                 # 当前魔法索引（默认第一个）
        self.magic = list(magic_data.keys())[self.magic_index]  # 魔法名称
        self.can_switch_magic = True         # 是否可以切换魔法
        self.magic_switch_time = None        # 上次切换魔法的时间戳

        # ── 属性系统 ──
        # stats: 当前五维属性值（生命/能量/攻击/魔法/速度）
        self.stats = {
            'health': 200,
            'energy': 100,
            'attack': 15,
            'magic': 5,
            'speed': 300
        }
        # max_stats: 各属性可达到的上限值
        self.max_stats = {
            'health': 600,
            'energy': 300,
            'attack': 30,
            'magic': 15,
            'speed': 720
        }
        # upgrade_cost: 各属性下一次升级所需的经验值
        self.upgrade_cost = {
            'health': 100,
            'energy': 100,
            'attack': 100,
            'magic': 100,
            'speed': 100
        }
        self.health = self.stats['health']    # 当前生命值（初始为最大值）
        self.energy = self.stats['energy']    # 当前能量值（初始为最大值）
        self.speed = self.stats['speed']      # 当前移动速度（像素/秒）
        self.exp = 0                          # 当前经验值

        # ── 受击无敌计时（短暂无敌，区别于全局无敌模式） ──
        self.vulnerable = True               # 是否可被伤害（False 时为受击无敌状态）
        self.hurt_time = None                # 上次受伤的时间戳（毫秒）
        self.invulnerability_duration = 500  # 受击无敌持续时间（毫秒，0.5秒）

        # ── 音效 ──
        self.weapon_attack_sound = res.get_sound('../audio/sword.wav', volume=0.2)
        if self.weapon_attack_sound is None:
            print('[WARN] Failed to load weapon attack sound')
        self.invincible_sound = res.get_sound('../audio/invincible.ogg', volume=0.5)

        # ── 全局无敌模式（按空格键激活的爆发状态） ──
        self.invincible = False              # 是否处于无敌状态
        self.invincible_start_time = None    # 无敌模式开始的时间戳
        self.invincible_cooldown_until = 0   # 冷却结束的时间戳（在此之前不能再次激活）
        self._invincible_keys_released = True  # 空格键是否已释放（防止按住连续触发）

    # ── Asset Loading ─────────────────────────────────────────────────

    def import_player_assets(self):
        """导入玩家的所有动画帧图像

        从 graphics/player/ 目录下按子文件夹名称（对应各动画状态）
        加载所有帧图像到 self.animations 字典中。

        动画状态包括 12 种：
          - 移动态: up / down / left / right（四方向行走）
          - 空闲态: up_idle / down_idle / left_idle / right_idle（站立不动）
          - 攻击态: up_attack / down_attack / left_attack / right_attack（攻击动画）

        每个状态对应一个图像列表（多帧循环播放）。
        """
        res = ResourceManager.instance()
        character_path = '../graphics/player'
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
            'right_attack': [], 'left_attack': [], 'up_attack': [], 'down_attack': [],
        }

        # 遍历每种动画状态，从对应文件夹加载所有图片
        for animation in self.animations.keys():
            full_path = character_path + '/' + animation
            self.animations[animation] = res.get_folder_images(full_path)

    # ── Input ─────────────────────────────────────────────────────────

    def input(self):
        """处理玩家的键盘与鼠标输入

        仅在非攻击状态（self.attacking == False）时响应输入。
        攻击动画期间禁止移动和新操作，保证攻击动作完整播放。

        输入绑定：
          - WASD / 方向键：移动并更新朝向状态
          - 鼠标左键：近战攻击
          - 鼠标右键：施放魔法
          - Q 键：切换武器（循环）
          - E 键：切换魔法（循环）
          - 空格键：激活无敌模式（限时爆发状态，有冷却和代价）

        方法特点：
          方向处理使用 elif 结构，保证一个方向优先（不产生对角线混合状态）。
          攻击/魔法触发时会立即清零方向向量，使角色在攻击时静止。
        """
        if not self.attacking:
            keys = pygame.key.get_pressed()

            # ── 方向移动（Y 轴：上/下） ──
            # 使用 elif 保证上/下只有一个生效，不会同时为 -1 和 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.direction.y = -1   # 向上移动（Y 轴减小）
                self.status = 'up'
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.direction.y = 1    # 向下移动（Y 轴增大）
                self.status = 'down'
            else:
                self.direction.y = 0    # 未按方向键，无垂直移动

            # ── 方向移动（X 轴：左/右） ──
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.direction.x = 1    # 向右移动（X 轴增大）
                self.status = 'right'
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.direction.x = -1   # 向左移动（X 轴减小）
                self.status = 'left'
            else:
                self.direction.x = 0    # 未按方向键，无水平移动

            # ── 近战攻击（鼠标左键） ──
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:  # left click
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()  # 记录攻击时间戳
                self.create_attack()    # 调用回调，在玩家前方生成攻击判定精灵
                if self.weapon_attack_sound:
                    self.weapon_attack_sound.play()  # 播放挥剑音效
                # 攻击时冻结移动，防止攻击动画期间角色滑步
                self.direction.x = 0
                self.direction.y = 0

            # ── 魔法攻击（鼠标右键） ──
            if mouse_buttons[2]:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()

                style = list(magic_data.keys())[self.magic_index]       # 魔法样式名称
                strength = list(magic_data.values())[
                    self.magic_index]['strength'] + self.stats['magic'] # 总魔法强度 = 法术基础 + 角色魔法属性
                cost = list(magic_data.values())[self.magic_index]['cost']  # 魔法消耗能量值
                self.create_magic(style, strength, cost)  # 调用回调创建魔法精灵
                # 施法时也冻结移动
                self.direction.x = 0
                self.direction.y = 0

            # ── 切换武器（Q 键） ──
            # can_switch_weapon 用于冷却判断，防止快速连按误切换
            if keys[pygame.K_q] and self.can_switch_weapon:
                self.can_switch_weapon = False
                self.weapon_switch_time = pygame.time.get_ticks()

                # 循环切换：到达列表末尾时回到起点
                if self.weapon_index < len(list(weapon_data.keys())) - 1:
                    self.weapon_index += 1
                else:
                    self.weapon_index = 0

                self.weapon = list(weapon_data.keys())[self.weapon_index]

            # ── 切换魔法（E 键） ──
            if keys[pygame.K_e] and self.can_switch_magic:
                self.can_switch_magic = False
                self.magic_switch_time = pygame.time.get_ticks()

                if self.magic_index < len(list(magic_data.keys())) - 1:
                    self.magic_index += 1
                else:
                    self.magic_index = 0

                self.magic = list(magic_data.keys())[self.magic_index]

            # ── 无敌模式（空格键激活） ──
            # 设计原则：
            #   1. 只能"激活"，到期后自动结束（30 秒），不可手动关闭
            #   2. 结束后进入 5 分钟冷却，冷却期间无法再次激活
            #   3. 结束时有代价惩罚（损失 50% 当前生命 + 清空能量）
            #   4. 使用 _invincible_keys_released 防止按键连发
            if keys[pygame.K_SPACE]:
                if self._invincible_keys_released:
                    # 只有按键从释放->按下时触发一次，按住不放不会重复触发
                    self._invincible_keys_released = False
                    if not self.invincible:
                        now = pygame.time.get_ticks()
                        if now >= self.invincible_cooldown_until:
                            # ── 激活无敌模式 ──
                            self.invincible = True
                            self.invincible_start_time = now
                            # 停止当前背景音乐，替换为无敌音效（循环播放）
                            pygame.mixer.music.stop()
                            if self.invincible_sound:
                                self.invincible_sound.play(-1)  # -1 表示无限循环
            else:
                # 空格键已释放，允许下次按下时再次判断
                self._invincible_keys_released = True

    # ── Status ────────────────────────────────────────────────────────

    def get_status(self):
        """更新玩家的动画状态字符串（状态机核心逻辑）

        状态由三部分组合：方向 + 姿态后缀。
        姿态后缀为空（移动）或 '_idle'（静止）或 '_attack'（攻击）。

        状态转换规则:
          1. 移动状态：由 input() 直接设置，如 'down'、'right'
          2. 空闲状态：当方向向量为零且不处于攻击时，追加 '_idle'
             - 'down' -> 'down_idle'
          3. 攻击状态：攻击时，将 '_idle' 替换为 '_attack'，或直接追加 '_attack'
             - 'down_idle' -> 'down_attack'
             - 'down' -> 'down_attack'
          4. 攻击结束：将 '_attack' 去掉，回到移动/空闲态

        此方法每帧由 update() 调用，配合 cooldowns() 中 self.attacking
        的变化，自动完成状态转换。
        """
        if self.direction.x == 0 and self.direction.y == 0:
            # 角色静止不动时，如果当前状态不是 idle 或 attack，追加 _idle
            if 'idle' not in self.status and 'attack' not in self.status:
                self.status = self.status + '_idle'

            if self.attacking:
                # 攻击期间：禁止移动
                self.direction.x = 0
                self.direction.y = 0
                # 如果状态中还没有攻击标记，则加上 _attack
                if 'attack' not in self.status:
                    if 'idle' in self.status:
                        # 替换 idle 后缀为 attack
                        self.status = self.status.replace('_idle', '_attack')
                    else:
                        # 直接从移动态追加 attack
                        self.status = self.status + '_attack'
            else:
                # 攻击结束后，移除攻击后缀回到普通状态
                if 'attack' in self.status:
                    self.status = self.status.replace('_attack', '')

    # ── Cooldowns ─────────────────────────────────────────────────────

    def cooldowns(self):
        """管理所有计时冷却状态（每帧由 update 调用）

        同时管理四组独立的冷却计时器：
          1. 攻击冷却：攻击后等待 weapon_data 中定义的冷却时间 + 基础冷却
          2. 武器切换冷却：200ms 内不能连续切换
          3. 魔法切换冷却：200ms 内不能连续切换
          4. 受击无敌冷却：受伤后 500ms 内不可再次被伤害

        所有冷却均使用 pygame.time.get_ticks() 返回的毫秒时间戳判断。
        """
        current_time = pygame.time.get_ticks()

        # 攻击冷却：攻击动作持续总时长 = 基础攻击冷却(400ms) + 武器自身额外冷却
        if self.attacking:
            if current_time - self.attack_time >= self.attack_cooldown + weapon_data[self.weapon]['cooldown']:
                self.attacking = False
                self.destroy_attack()  # 通知上层销毁攻击判定精灵

        # 武器切换冷却
        if not self.can_switch_weapon:
            if current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
                self.can_switch_weapon = True  # 恢复切换能力

        # 魔法切换冷却
        if not self.can_switch_magic:
            if current_time - self.magic_switch_time >= self.switch_duration_cooldown:
                self.can_switch_magic = True

        # 受击无敌冷却：受伤后短暂不可被再次伤害
        if not self.vulnerable:
            if current_time - self.hurt_time >= self.invulnerability_duration:
                self.vulnerable = True  # 恢复可受击状态

    # ── Animation ─────────────────────────────────────────────────────

    def animate(self, dt):
        """每帧更新玩家的动画图像并应用视觉效果

        在基类 Entity.animate() 的帧推进基础上增加了三层处理：
          1. 重定位 rect：使用 hitbox 中心（物理位置）来确定渲染位置
          2. 受伤闪烁：vulnerable=False 时，通过正弦波亮度闪烁表示无敌
          3. 无敌金色覆盖：invincible=True 时，在图像上叠加半透明金色层

        参数:
            dt (float): 帧时间间隔（秒），用于帧率无关的动画
        """
        # 第 1 步：委托基类进行帧索引推进和图像切换
        super().animate(dt)

        # 第 2 步：将渲染矩形 rect 的中心对齐到碰撞箱 hitbox 的中心
        # 确保动画图像的渲染位置与物理碰撞位置一致
        self.rect = self.image.get_rect(center=self.hitbox.center)

        # 第 3 步：受击闪烁效果
        # 当 vulnerable=False（即刚受伤后的短暂无敌期），
        # 使用正弦波让 alpha 值在 0 和 255 之间快速切换，产生闪烁视觉效果
        if not self.vulnerable:
            alpha = self.wave_value()       # 返回 255 或 0（交替闪烁）
            self.image.set_alpha(alpha)     # 设置透明度
        else:
            self.image.set_alpha(255)       # 正常情况下完全不透明

        # 第 4 步：无敌模式金色覆盖层
        # 在角色图像上叠加一层半透明金色，视觉效果上区分于普通受击闪烁
        if self.invincible:
            # 创建一个与角色图像相同大小的透明 Surface
            gold_overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            # 填充金黄色 (R=255, G=200, B=0, Alpha=80)，80 为半透明
            gold_overlay.fill((255, 200, 0, 80))
            # 复制原图避免修改原帧数据
            self.image = self.image.copy()
            # 使用 BLEND_RGBA_ADD 模式叠加金色，产生发光效果
            self.image.blit(gold_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # ── Damage Calculation ────────────────────────────────────────────

    def get_full_weapon_damage(self):
        """计算玩家的最终武器伤害值

        最终伤害 = 角色攻击力 + 武器固有伤害
        如果处于无敌模式，再乘以无敌攻击倍率（INVINCIBLE_ATTACK_MULT）。

        返回:
            float: 最终武器伤害值（可能包含无敌模式加成）
        """
        base_damage = self.stats['attack']                     # 角色自身攻击属性
        weapon_damage = weapon_data[self.weapon]['damage']     # 武器额外伤害
        damage = base_damage + weapon_damage
        if self.invincible:
            damage *= INVINCIBLE_ATTACK_MULT    # 无敌期间伤害翻倍（或按配置倍率）
        return damage

    def get_full_magic_damage(self):
        """计算玩家的最终魔法伤害值

        最终伤害 = 角色魔法属性 + 法术固有强度
        如果处于无敌模式，再乘以无敌攻击倍率。

        返回:
            float: 最终魔法伤害值
        """
        base_damage = self.stats['magic']                      # 角色自身魔法属性
        spell_damage = magic_data[self.magic]['strength']      # 法术基础强度
        damage = base_damage + spell_damage
        if self.invincible:
            damage *= INVINCIBLE_ATTACK_MULT
        return damage

    # ── Upgrade Helpers ───────────────────────────────────────────────

    def get_value_by_index(self, idx):
        """按索引获取 stats 中对应属性的当前值（供 UI 升级面板使用）

        参数:
            idx (int): 属性索引（0=health, 1=energy, 2=attack, 3=magic, 4=speed）

        返回:
            int: 对应属性的当前数值
        """
        return list(self.stats.values())[idx]

    def get_cost_by_index(self, idx):
        """按索引获取对应属性的下一次升级所需经验值

        参数:
            idx (int): 属性索引

        返回:
            int: 升级所需经验值
        """
        return list(self.upgrade_cost.values())[idx]

    # ── Weapon Cycling ────────────────────────────────────────────────

    def cycle_weapon(self, direction):
        """通过鼠标滚轮切换武器（UI 交互）

        配合升级面板中的滚轮事件，支持向前/向后循环切换武器。
        direction > 0 切到下一把，direction < 0 切到上一把。

        参数:
            direction (int): 滚轮方向，正数=下一个，负数=上一个
        """
        if not self.can_switch_weapon:
            return  # 冷却中不可切换
        self.can_switch_weapon = False
        self.weapon_switch_time = pygame.time.get_ticks()
        weapon_keys = list(weapon_data.keys())
        # 使用取模运算实现双向循环切换
        if direction > 0:
            self.weapon_index = (self.weapon_index + 1) % len(weapon_keys)
        else:
            self.weapon_index = (self.weapon_index - 1) % len(weapon_keys)
        self.weapon = weapon_keys[self.weapon_index]

    # ── Energy Recovery ───────────────────────────────────────────────

    def energy_recovery(self, dt):
        """能量自然恢复：每秒恢复量等于角色魔法属性值

        能量不会超过最大值（stats['energy']）。
        dt 用于帧率无关的平滑恢复。

        参数:
            dt (float): 帧时间间隔（秒）
        """
        if self.energy < self.stats['energy']:
            # 恢复量 = 魔法属性 * 帧间隔时间
            self.energy += self.stats['magic'] * dt
        else:
            # 上限钳制，防止浮点误差导致超过最大值
            self.energy = self.stats['energy']

    # ── Invincible Expiry ─────────────────────────────────────────────

    def _check_invincible_expiry(self):
        """无敌模式到期检测（每帧由 update 调用）

        如果玩家处于无敌状态且持续时间超过配置的 INVINCIBLE_DURATION（30 秒），
        自动调用 _end_invincibility() 结束无敌状态。
        """
        if not self.invincible or self.invincible_start_time is None:
            return  # 未处于无敌状态，无需检查
        elapsed = pygame.time.get_ticks() - self.invincible_start_time
        if elapsed >= INVINCIBLE_DURATION:
            self._end_invincibility()

    def _end_invincibility(self):
        """结束无敌模式并执行代价惩罚

        流程：
          1. 关闭无敌状态，清空启动时间
          2. 设置 5 分钟冷却（在此期间无法再次激活）
          3. 代价惩罚：失去 50% 当前生命值（至少保留 1 HP）
          4. 代价惩罚：清空全部能量
          5. 停止无敌音效，根据当前音乐状态恢复背景音乐

        设计意图：
          无敌模式提供 30 秒的强力爆发（高移速 + 高伤害 + 免疫伤害），
          但在到期时必须支付沉重代价，防止玩家无脑滥用。
        """
        # ── 状态重置 ──
        self.invincible = False
        self.invincible_start_time = None

        # ── 设置冷却（INVINCIBLE_COOLDOWN 毫秒，默认 5 分钟） ──
        self.invincible_cooldown_until = pygame.time.get_ticks() + INVINCIBLE_COOLDOWN

        # ── 生命代价：损失当前生命的 50%（至少保留 1 点 HP） ──
        # INVINCIBLE_COST_HEALTH = 0.5（配置值）
        self.health = max(1, int(self.health * (1 - INVINCIBLE_COST_HEALTH)))

        # ── 能量代价：全部清空 ──
        self.energy = 0

        # ── 恢复背景音乐 ──
        # 停止无敌音效
        if self.invincible_sound:
            self.invincible_sound.stop()
        # 根据当前游戏音乐状态（普通/BOSS）恢复对应的 BGM
        if MusicState.get() == 1:  # BOSS 战状态
            bgm_path = get_path('../audio/boss_bgm.ogg')
            vol = 0.5
        else:  # 普通地图状态
            bgm_path = get_path('../audio/game_bgm.ogg')
            vol = 0.3
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.set_volume(vol)
        pygame.mixer.music.play(-1)  # -1 表示无限循环播放

    def get_invincible_status(self):
        """获取无敌模式当前状态（供 UI 界面显示）

        返回值三元组 (state, seconds_remaining, cooldown_remaining) 分别表示：
          - state: 当前状态字符串
            - 'active':   无敌模式进行中
            - 'cooldown': 冷却中
            - 'ready':    就绪，可再次激活
          - seconds_remaining:   无敌剩余秒数（active 时有效）
          - cooldown_remaining:  冷却剩余秒数（cooldown 时有效）

        返回:
            tuple[str, float, float]: (状态标签, 剩余秒数, 冷却剩余秒数)
        """
        now = pygame.time.get_ticks()
        # 无敌模式激活中：计算剩余时间
        if self.invincible and self.invincible_start_time is not None:
            remaining = max(0, (INVINCIBLE_DURATION - (now - self.invincible_start_time)) / 1000.0)
            return ('active', remaining, 0)
        # 冷却中：计算剩余冷却时间
        if now < self.invincible_cooldown_until:
            cd_remaining = max(0, (self.invincible_cooldown_until - now) / 1000.0)
            return ('cooldown', 0, cd_remaining)
        # 就绪状态：随时可以激活
        return ('ready', 0, 0)

    # ── Main Update ───────────────────────────────────────────────────

    def update(self, dt):
        """玩家主更新方法（每帧由游戏主循环调用一次）

        执行顺序：
          1. input()              — 处理键盘和鼠标输入
          2. cooldowns()          — 更新所有冷却状态
          3. get_status()         — 更新动画状态字符串
          4. animate(dt)          — 更新动画帧
          5. move()               — 执行移动和碰撞检测（含无敌移速加成）
          6. energy_recovery(dt)  — 能量自然恢复
          7. _check_invincible_expiry() — 检测无敌模式是否到期

        参数:
            dt (float): 帧时间间隔（秒），由主循环传入
        """
        self.input()
        self.cooldowns()
        self.get_status()
        self.animate(dt)

        # ── 移动速度应用（含无敌模式加速） ──
        speed = self.stats['speed']       # 角色基础移动速度（像素/秒）
        if self.invincible:
            speed *= INVINCIBLE_SPEED_MULT  # 无敌期间移速乘以配置倍率（如 1.5 倍）

        self.move(speed, self.pos, dt)    # 执行移动（含碰撞检测，见 Entity.move）
        self.energy_recovery(dt)          # 每秒自动恢复能量
        self._check_invincible_expiry()   # 检测无敌 30 秒到期
