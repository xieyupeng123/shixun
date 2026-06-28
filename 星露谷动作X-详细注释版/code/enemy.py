# -*- coding: utf-8 -*-
"""
enemy.py — 敌人类（含普通敌人和Boss）

定义 Enemy 类，继承自 Entity 基类。
实现了敌人的 AI 状态机（idle → move → attack → hit → death），
包含路径追踪、Boss 多阶段机制、受击无敌、击退反馈等完整行为。
"""

import pygame

from settings import monster_data, BOSS_PHASE_DATA
from entity import Entity
from pathfinding_utils import astar, pos_to_grid, grid_to_pos
from resource_manager import ResourceManager


class Enemy(Entity):
    """
    敌人类，管理单个敌人的全部生命周期。

    AI 状态机流转：
        idle（闲置） → move（追击） → attack（攻击） → hit（受击） → death（死亡）。

    扩展功能：
        - Boss 多阶段属性缩放与颜色染色
        - A* 寻路网格路径追踪
        - 受击无敌帧与击退反馈
        - 死亡时生成经验球粒子
    """

    def __init__(self, monster_name, pos, groups, obstacle_sprites, damage_player, trigger_death_particles, add_exp, trigger_exp_particles=None, pathfinding_grid=None, tile_size=None, is_boss=False, boss_phase=1, on_boss_killed=None):
        """
        初始化敌人实例。

        参数:
            monster_name (str): 怪物名称（如 'squid'、'raccoon'），用于读取 monster_data 配置
            pos (tuple): 初始生成位置的像素坐标 (x, y)
            groups (list[pygame.sprite.Group]): 所有要加入的精灵组，如可见组、碰撞组等
            obstacle_sprites (pygame.sprite.Group): 障碍物精灵组，用于碰撞检测
            damage_player (callable): 回调函数，调用时对玩家造成伤害：damage_player(伤害量, 攻击类型)
            trigger_death_particles (callable): 回调函数，触发死亡粒子特效：trigger_death_particles(位置, 怪物名)
            add_exp (callable): 回调函数，向玩家添加经验值：add_exp(经验量)
            trigger_exp_particles (callable, optional): 回调函数，生成经验球粒子：trigger_exp_particles(死亡位置, 玩家位置, 经验量)
            pathfinding_grid (list[list[int]], optional): 二维寻路网格（0=可行走，1=障碍物），用于 A* 寻路
            tile_size (int, optional): 单个瓦片的像素尺寸，用于坐标与网格之间的转换
            is_boss (bool): 是否为 Boss 敌人，为 True 则启用多阶段属性缩放和颜色染色
            boss_phase (int): Boss 当前阶段编号（1 起始），影响属性倍率和染色颜色
            on_boss_killed (callable, optional): Boss 死亡时的回调函数，接收死亡位置参数
        """
        super().__init__(groups, pos)
        res = ResourceManager.instance()

        # ── 基础属性 ──────────────────────────────────────────────────────
        self.sprite_type = 'enemy'  # 精灵类型标识，用于碰撞分组

        # ── 图像资源加载 ──────────────────────────────────────────────────
        self.import_graphics(monster_name)
        self.status = 'idle'  # AI 状态机初始状态：闲置
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)

        # ── 移动与碰撞箱 ─────────────────────────────────────────────────
        if is_boss:
            # Boss 精灵尺寸为 240x240，使用较小的碰撞箱（48x48）
            # 避免跨越多个障碍物格子产生连锁碰撞
            self.hitbox = pygame.Rect(0, 0, 48, 48)
            self.hitbox.center = self.rect.center
        else:
            self.hitbox = self.rect.inflate(0, -10)  # 普通敌人碰撞箱在垂直方向收缩 10 像素
        self.obstacle_sprites = obstacle_sprites
        self.pos = pygame.math.Vector2(self.rect.center)

        # ── Boss 身份标识 ────────────────────────────────────────────────
        self.is_boss = is_boss
        self.boss_phase = boss_phase         # 当前阶段编号（1, 2, 3...）
        self.on_boss_killed = on_boss_killed # Boss 死亡时的特殊回调

        # ── 属性数值（支持 Boss 阶段倍率缩放） ──────────────────────────
        self.monster_name = monster_name
        monster_info = monster_data[self.monster_name]          # 从配置表读取怪物基础属性
        stat_mult = BOSS_PHASE_DATA[boss_phase]['stat_mult'] if is_boss else 1.0  # Boss 阶段属性倍率
        self.health = int(monster_info['health'] * stat_mult)   # 生命值（受阶段倍率影响）
        self.exp = monster_info['exp']                          # 击杀经验值
        self.speed = monster_info['speed']                      # 移动速度（不受阶段影响）
        self.attack_damage = int(monster_info['damage'] * stat_mult)  # 攻击力（受阶段倍率影响）
        self.resistance = monster_info['resistance']            # 击退抗性（正值越大越难被击退）
        self.attack_radius = monster_info['attack_radius']      # 攻击判定半径（像素）
        self.notice_radius = monster_info['notice_radius']      # 索敌半径（像素）

        # ── 经验球回调 ──────────────────────────────────────────────────
        self.trigger_exp_particles = trigger_exp_particles      # 生成经验球粒子的回调
        self.last_player_pos = None                             # 上一帧玩家位置（用于经验球追踪）
        self.attack_type = monster_info['attack_type']          # 攻击类型（'weapon' 或 'magic'）

        # ── 与玩家的交互 ────────────────────────────────────────────────
        self.can_attack = True           # 是否允许攻击（由攻击冷却控制）
        self.attack_time = None          # 上次攻击的时间戳（毫秒）
        self.attack_cooldown = 400       # 攻击冷却时间（毫秒）
        self.damage_player = damage_player          # 对玩家造成伤害的回调
        self.trigger_death_particles = trigger_death_particles  # 触发死亡粒子特效的回调
        self.add_exp = add_exp                      # 添加经验值的回调

        # ── 受击无敌计时 ────────────────────────────────────────────────
        self.vulnerable = True               # 是否可受到伤害（受击后变为 False）
        self.hit_time = None                 # 上次受击的时间戳（毫秒）
        self.invisibility_duration = 300     # 受击后无敌持续时间（毫秒）
        self._knockback_applied = False      # 当前受击是否已应用过击退（防止每帧重复击退）

        # ── 音效（通过 ResourceManager 缓存加载） ──────────────────────
        self.hit_sound = res.get_sound('../audio/hit.wav', volume=0.6)
        self.death_sound = res.get_sound('../audio/death.wav', volume=0.6)
        self.attack_sound = res.get_sound(monster_data[self.monster_name]['attack_sound'], volume=0.3)

        # ── A* 寻路相关 ─────────────────────────────────────────────────
        self.pathfinding_grid = pathfinding_grid  # 二维网格引用（0=可行走，1=障碍物）
        self.tile_size = tile_size                # 每个瓦片的像素尺寸
        self.path = []                            # 当前路径节点列表（世界坐标网格坐标）
        self.last_path_time = 0                   # 上次路径重算的时间戳（毫秒）
        self.path_recalc_interval = 500           # 路径重算间隔（毫秒），避免每帧都重新计算
        self._last_player_grid = None             # 玩家上一帧所在的网格坐标，用于判断是否需重算路径

    # ═══════════════════════════════════════════════════════════════════════
    # 图像资源加载
    # ═══════════════════════════════════════════════════════════════════════

    def import_graphics(self, name):
        """
        从磁盘加载怪物的所有动画帧图像。

        按动画状态（idle / move / attack）分别加载对应文件夹中的图片序列。
        使用 ResourceManager 的缓存机制避免重复加载。

        参数:
            name (str): 怪物名称，对应 ../graphics/monsters/<name>/ 目录下的子文件夹
        """
        res = ResourceManager.instance()
        self.animations = {'idle': [], 'move': [], 'attack': []}
        for animation in self.animations.keys():
            # 从 ../graphics/monsters/<name>/idle（或 move、attack）目录加载所有 PNG 图片
            self.animations[animation] = res.get_folder_images(
                f'../graphics/monsters/{name}/' + animation)

    # ═══════════════════════════════════════════════════════════════════════
    # 玩家检测与距离计算
    # ═══════════════════════════════════════════════════════════════════════

    def get_player_distance_direction(self, player):
        """
        计算敌人与玩家之间的距离和方向向量。

        参数:
            player (Player): 玩家对象，需要具备 rect.center 属性

        返回:
            tuple: (distance, direction)
                - distance (float): 敌人中心到玩家中心的欧几里得距离（像素）
                - direction (pygame.math.Vector2): 从敌人指向玩家的单位方向向量
        """
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(player.rect.center)
        distance = (player_vec - enemy_vec).magnitude()

        if distance > 0:
            direction = (player_vec - enemy_vec).normalize()
        else:
            direction = pygame.math.Vector2()

        return (distance, direction)

    # ═══════════════════════════════════════════════════════════════════════
    # AI 状态机 — 状态判定
    # ═══════════════════════════════════════════════════════════════════════

    def get_status(self, player):
        """
        根据与玩家的距离和攻击冷却判定当前 AI 状态。

        AI 状态流转规则（按优先级从高到低）：
            1. attack（攻击） — 玩家在攻击半径内 且 攻击冷却已结束
            2. move（追击）   — 玩家在索敌半径内但超出攻击半径
            3. idle（闲置）   — 玩家超出索敌半径

        特殊说明：
            - 当处于攻击半径内但攻击仍在冷却时，保持上次状态不变，
              等待攻击动画播放完毕。
            - 非 move 状态时清空路径缓存，避免残留路径干扰。

        参数:
            player (Player): 玩家对象，用于计算距离
        """
        distance = self.get_player_distance_direction(player)[0]

        if distance <= self.attack_radius and self.can_attack:
            # 玩家进入攻击范围且冷却结束 → 切换到攻击状态，重置动画帧
            if self.status != 'attack':
                self.frame_index = 0
            self.status = 'attack'
        elif distance <= self.attack_radius and not self.can_attack:
            # 玩家在攻击范围内但攻击仍在冷却 → 保持当前状态等待
            pass
        elif distance <= self.notice_radius:
            # 玩家在索敌半径内但超出攻击半径 → 切换为追击状态
            self.status = 'move'
        else:
            # 玩家超出索敌半径 → 切换为闲置状态
            self.status = 'idle'
        # 清除路径缓存：非移动状态下不需要寻路
        if self.status != 'move':
            self.path = []

    # ═══════════════════════════════════════════════════════════════════════
    # AI 状态机 — 状态执行动作
    # ═══════════════════════════════════════════════════════════════════════

    def actions(self, player):
        """
        根据当前 AI 状态执行对应的动作逻辑。

        各状态行为：
            - attack（攻击）：对玩家造成伤害，播放攻击音效，进入攻击冷却
            - move（追击）：通过 A* 寻路计算路径并朝向目标移动；若路径不可用则直接朝玩家移动
            - idle（闲置）：方向向量归零，停止移动

        路径重算触发条件：
            1. 当前路径为空
            2. 距离上次重算超过 path_recalc_interval（500ms）
            3. 玩家移动到了新的网格格子

        参数:
            player (Player): 玩家对象
        """
        now = pygame.time.get_ticks()
        if self.status == 'attack':
            # ── 攻击状态：造成伤害，触发冷却 ────────────────────────────
            if self.can_attack:
                self.can_attack = False          # 进入攻击冷却
                self.attack_time = now           # 记录攻击时间戳
                self.damage_player(self.attack_damage, self.attack_type)  # 对玩家造成伤害
                if self.attack_sound:
                    self.attack_sound.play()     # 播放攻击音效

        elif self.status == 'move':
            # ── 追击状态：A* 寻路追踪玩家 ────────────────────────────────
            recalc = False
            # 判定是否需要重新计算路径
            if not self.path or now - self.last_path_time > self.path_recalc_interval:
                recalc = True  # 路径为空或超时需重算
            else:
                # 玩家是否移动到了新格子
                current_player_grid = pos_to_grid(player.rect.center, self.tile_size)
                if self._last_player_grid != current_player_grid:
                    recalc = True  # 玩家位置变化需重算

            if recalc and self.pathfinding_grid is not None:
                # 将像素坐标转换为网格坐标
                start = pos_to_grid(self.rect.center, self.tile_size)
                goal = pos_to_grid(player.rect.center, self.tile_size)
                self._last_player_grid = goal
                # 执行 A* 寻路算法
                path = astar(self.pathfinding_grid, start, goal)
                if path and len(path) > 1:
                    self.path = path[1:]  # 跳过当前所在节点（第一个元素），从下一个节点开始移动
                else:
                    self.path = []  # 无法到达目标，清空路径
                self.last_path_time = now  # 更新重算时间戳

            # ── 路径跟随（沿路径节点移动） ──────────────────────────────
            if self.path:
                next_node = self.path[0]                          # 获取路径上的下一个目标节点
                next_pos = grid_to_pos(next_node, self.tile_size) # 将网格坐标转回像素坐标
                vec_to_next = pygame.math.Vector2(next_pos) - pygame.math.Vector2(self.rect.center)
                if vec_to_next.length() < 4:  # 距离当前节点足够近（<4像素），移到下一个节点
                    self.path.pop(0)
                    if self.path:
                        next_node = self.path[0]
                        next_pos = grid_to_pos(next_node, self.tile_size)
                        vec_to_next = pygame.math.Vector2(next_pos) - pygame.math.Vector2(self.rect.center)
                if vec_to_next.length() > 0:
                    self.direction = vec_to_next.normalize()  # 朝向下一节点
                else:
                    self.direction = pygame.math.Vector2()
            else:
                # 回退方案：无可用路径时直接朝玩家直线移动
                self.direction = self.get_player_distance_direction(player)[1]
        else:
            # ── 闲置状态：停止移动 ──────────────────────────────────────
            self.direction = pygame.math.Vector2()

    # ═══════════════════════════════════════════════════════════════════════
    # 动画更新
    # ═══════════════════════════════════════════════════════════════════════

    def animate(self, dt):
        """
        更新敌人的动画帧，并处理特殊视觉效果。

        普通敌人：委托基类 Entity 的 animate() 逐帧推进动画。
        Boss 敌人：额外叠加当前阶段的颜色染色（RGBA 叠加混合）。
        无敌状态：通过 alpha 闪烁效果（set_alpha 闪烁）表现受击无敌。

        参数:
            dt (float): 上一帧到当前帧的时间差（秒），用于帧率无关的动画
        """
        # 委托基类推进动画帧
        super().animate(dt)

        # Boss 阶段颜色染色
        if self.is_boss:
            phase_color = BOSS_PHASE_DATA[self.boss_phase]['color']
            if phase_color is not None:
                tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                tint.fill((*phase_color, 80))                       # 半透明染色层，alpha=80
                self.image = self.image.copy()
                self.image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)  # 叠加混合

        # 无敌闪烁效果（受击后短暂闪烁）
        if not self.vulnerable:
            alpha = self.wave_value()  # 通过正弦波计算 alpha 值，产生闪烁效果
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    # ═══════════════════════════════════════════════════════════════════════
    # 冷却计时
    # ═══════════════════════════════════════════════════════════════════════

    def cooldown(self):
        """
        更新攻击冷却和受击无敌冷却。

        攻击冷却：攻击后经过 attack_cooldown（400ms）才能再次攻击。
        受击无敌：受击后经过 invisibility_duration（300ms）恢复可受伤状态，
                 同时重置击退标记，允许下一次受击产生击退效果。
        """
        current_time = pygame.time.get_ticks()
        # 攻击冷却计时
        if not self.can_attack:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.can_attack = True  # 冷却结束，允许再次攻击

        # 受击无敌冷却计时
        if not self.vulnerable:
            if current_time - self.hit_time >= self.invisibility_duration:
                self.vulnerable = True          # 恢复可受伤状态
                self._knockback_applied = False  # 重置击退标记

    # ═══════════════════════════════════════════════════════════════════════
    # 受伤与死亡
    # ═══════════════════════════════════════════════════════════════════════

    def get_damage(self, player, attack_type):
        """
        受到伤害时的处理逻辑。

        仅在 vulnerable（可受伤）状态下生效。
        根据攻击类型扣除对应伤害量：
            - 'weapon'：使用玩家的武器伤害
            - 'magic'：使用玩家的魔法伤害

        受击后触发：
            - 播放受击音效
            - 计算击退方向（从玩家指向敌人自身）
            - 进入无敌状态（vulnerable = False），持续 invisibility_duration 毫秒

        参数:
            player (Player): 攻击者（玩家）对象
            attack_type (str): 攻击类型，'weapon' 或 'magic'
        """
        if self.vulnerable:
            self.hit_sound.play()  # 播放受击音效
            self.direction = self.get_player_distance_direction(player)[1]  # 记录击退方向
            if attack_type == 'weapon':
                self.health -= player.get_full_weapon_damage()   # 减去武器伤害
            else:  # magic
                self.health -= player.get_full_magic_damage()    # 减去魔法伤害
            self.hit_time = pygame.time.get_ticks()  # 记录受伤时间戳
            self.vulnerable = False                   # 进入无敌状态

    def check_death(self):
        """
        检查生命值是否归零，执行死亡逻辑。

        死亡流程：
            1. 记录死亡位置
            2. 从所有精灵组中移除自身
            3. 触发死亡粒子特效
            4. 向玩家添加经验值
            5. 若存在经验球回调且记录了玩家位置，生成经验球粒子（飞向玩家）
            6. 播放死亡音效
            7. 若是 Boss，执行 on_boss_killed 回调
        """
        if self.health <= 0:
            death_pos = self.rect.center    # 记录死亡位置
            self.kill()                     # 从所有精灵组中移除
            self.trigger_death_particles(death_pos, self.monster_name)  # 生成死亡粒子特效
            self.add_exp(self.exp)          # 向玩家添加经验
            if self.trigger_exp_particles and self.last_player_pos:
                # 生成飞向玩家的经验球粒子
                self.trigger_exp_particles(death_pos, self.last_player_pos, self.exp)
            self.death_sound.play()         # 播放死亡音效
            # Boss 死亡特殊回调（如触发阶段转换、掉落奖励等）
            if self.is_boss and self.on_boss_killed:
                self.on_boss_killed(death_pos)

    # ═══════════════════════════════════════════════════════════════════════
    # 受击反馈 — 击退效果
    # ═══════════════════════════════════════════════════════════════════════

    def hit_reaction(self):
        """
        处理受击后的击退反馈。

        仅在不可受伤（无敌）状态下触发。
        击退方向为从敌人指向玩家的方向取反，大小受 resistance（击退抗性）影响。
        使用 _knockback_applied 标记确保每次受击只应用一次击退，
        避免因方向向量在 update 循环中被反复乘以 -resistance 导致失控。

        公式：direction = direction.normalize() * (-resistance)
             - resistance 越大，击退距离越远
             - 负号表示向后弹开（与朝向玩家方向相反）
        """
        if not self.vulnerable:
            if not self._knockback_applied and self.direction.magnitude() > 0:
                # 应用单次击退，方向为朝玩家方向的反方向 × 抗性系数
                self.direction = self.direction.normalize() * (-self.resistance)
                self._knockback_applied = True

    # ═══════════════════════════════════════════════════════════════════════
    # 主更新循环
    # ═══════════════════════════════════════════════════════════════════════

    def update(self, dt):
        """
        每帧更新敌人逻辑（由精灵组自动调用）。

        更新顺序：
            1. hit_reaction() — 处理击退效果
            2. move() — 根据速度和方向移动敌人
            3. animate(dt) — 更新动画帧
            4. cooldown() — 更新攻击和无敌冷却
            5. check_death() — 检查是否死亡

        参数:
            dt (float): 帧时间差（秒），用于帧率无关的移动和动画
        """
        self.hit_reaction()
        self.move(self.speed, self.pos, dt)  # 调用基类 Entity 的移动方法
        self.animate(dt)
        self.cooldown()
        self.check_death()

    def enemy_update(self, player):
        """
        由外部（如关卡更新循环）调用的 AI 更新入口。

        在 update() 之外单独调用，因为 AI 决策依赖玩家对象引用，
        需要在移动和动画之前先确定行为目标。

        执行顺序：
            1. get_status(player) — 根据距离判定 AI 状态
            2. actions(player) — 执行当前状态对应的动作
            3. 记录玩家位置 → 供死亡时生成追踪经验球使用

        参数:
            player (Player): 玩家对象，用于 AI 决策和目标追踪
        """
        self.get_status(player)   # 第一步：判定 AI 状态（idle / move / attack）
        self.actions(player)      # 第二步：执行状态对应的行为
        # 每次帧更新时记录玩家位置，以便死亡时经验球能朝玩家飞行
        self.last_player_pos = player.rect.center
