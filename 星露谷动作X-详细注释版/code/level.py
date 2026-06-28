import pygame
from settings import TILESIZE
from support import get_path
from random import randint
from weapon import Weapon
from ui import UI
from enemy import Enemy
from particles import AnimationPlayer
from magic import MagicPlayer
from upgrade import Upgrade
from map_manager import MapManager
from music_state import MusicState


# ── Combat Manager（战斗管理器）───────────────────────────────────────
class CombatManager:
    """战斗管理器：负责武器/魔法创建、攻击碰撞检测以及玩家受伤处理。

    将战斗逻辑从 Level 主类中抽离，使得地图逻辑与战斗逻辑职责分离。
    核心功能包括：
    - 创建与销毁武器（Weapon）和魔法攻击精灵
    - 检测攻击精灵与可攻击精灵之间的碰撞
    - 处理玩家受到敌人攻击时的伤害与无敌帧
    """

    def __init__(self, level):
        """初始化战斗管理器。

        参数:
            level: Level 主类实例，用于访问玩家、精灵组、粒子动画等资源。
        """
        self.level = level
        # 当前持有的武器实例（Weapon 对象），用于后续销毁
        self.current_attack = None
        # 攻击碰撞精灵组（武器/魔法产生的攻击判定区域）
        self.attack_sprites = pygame.sprite.Group()
        # 可被攻击的精灵组（敌人、草丛等）
        self.attackable_sprites = pygame.sprite.Group()

    def create_attack(self):
        """创建近战武器攻击。

        实例化一个 Weapon 对象，将其添加到 visible_sprites（可见）和
        attack_sprites（碰撞检测）两个精灵组中。
        """
        self.current_attack = Weapon(
            self.level.player, [self.level.visible_sprites, self.attack_sprites])

    def create_magic(self, style, strength, cost):
        """创建魔法攻击（治疗或火焰）。

        参数:
            style:   魔法类型，'heal' 为治疗，'flame' 为火焰。
            strength:魔法强度数值。
            cost:    魔法消耗（法力值）。
        """
        if style == 'heal':
            self.level.magic_player.heal(
                self.level.player, strength, cost, [self.level.visible_sprites])
        if style == 'flame':
            self.level.magic_player.flame(
                self.level.player, cost,
                [self.level.visible_sprites, self.attack_sprites])

    def destroy_attack(self):
        """销毁当前武器攻击精灵。

        将 current_attack 从所有精灵组中移除（kill），
        并将引用置为 None，表示本次攻击结束。
        """
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def player_attack_logic(self):
        """玩家攻击碰撞检测逻辑（每帧执行）。

        遍历所有攻击精灵（武器/魔法），检测它们与 attackable_sprites
        （敌人、草丛等）之间的碰撞：
        - 若碰撞目标是草丛（grass）：
            记录被摧毁的草丛位置（用于存档），生成草丛粒子特效，
            然后移除该草丛精灵。
        - 若碰撞目标是敌人或其他可攻击目标：
            调用目标精灵的 get_damage() 方法，传入玩家引用和攻击类型。
        """
        if self.attack_sprites:
            for attack_sprite in self.attack_sprites:
                collision_sprites = pygame.sprite.spritecollide(
                    attack_sprite, self.attackable_sprites, False)
                if collision_sprites:
                    for target_sprite in collision_sprites:
                        if target_sprite.sprite_type == 'grass':
                            pos = target_sprite.rect.center
                            self.level.destroyed_grass.append(
                                {'x': pos[0], 'y': pos[1]})
                            offset = pygame.math.Vector2(0, 75)
                            for leaf in range(randint(3, 6)):
                                self.level.animation_player.create_grass_particles(
                                    pos - offset, [self.level.visible_sprites])
                            target_sprite.kill()
                        else:
                            target_sprite.get_damage(
                                self.level.player, attack_sprite.sprite_type)

    def damage_player(self, amount, attack_type):
        """对玩家造成伤害（由敌人攻击触发）。

        参数:
            amount:     伤害数值（减血量）。
            attack_type:攻击类型字符串，用于生成对应的粒子特效。

        逻辑说明：
        - 若玩家处于无敌状态（invincible），直接返回，不扣血。
        - 若玩家处于可受伤状态（vulnerable），扣除 health，
          立即将 vulnerable 置为 False（进入受伤无敌帧），
          记录受伤时间（hurt_time），并生成受伤粒子特效。
        """
        player = self.level.player
        if player.invincible:
            return
        if player.vulnerable:
            player.health -= amount
            player.vulnerable = False
            player.hurt_time = pygame.time.get_ticks()
            self.level.animation_player.create_particles(
                attack_type, player.rect.center,
                [self.level.visible_sprites])


# ── Boss Manager（Boss 管理器）─────────────────────────────────────────
class BossManager:
    """Boss 管理器：负责 Boss 的生成、三阶段切换和胜利检测。

    设计说明：
    - Boss 在地图 CSV 中 ENTITY_BOSS_SPAWN 标记位置生成。
    - 三阶段系统：Boss 被击败后，会在同一位置以更高阶段重生，
      共 3 个阶段（1→2→3），每个阶段的 Boss 属性逐级增强。
    - 击败全部 3 个阶段后触发胜利（_trigger_victory = True）。
    """

    def __init__(self, level):
        """初始化 Boss 管理器。

        参数:
            level: Level 主类实例，用于访问精灵组、玩家、寻路网格等。
        """
        self.level = level
        # 当前活跃的 Boss 精灵引用（None 表示无存活 Boss）
        self.boss = None
        # 已击杀的 Boss 阶段数（每杀一次 +1，到达 3 触发胜利）
        self.boss_kills = 0
        # Boss 在地图上的固定生成位置像素坐标（由 MapManager 在加载时设定）
        self._boss_spawn_pos = None
        # 胜利标志，当 boss_kills >= 3 时置为 True，供 main.py 检测
        self._trigger_victory = False

    def spawn_boss(self, phase):
        """在地图标记位置生成指定阶段的 Boss。

        参数:
            phase: Boss 阶段编号（1、2 或 3），影响敌人的属性倍率。

        流程：
        1. 若 _boss_spawn_pos 未设置，直接返回（地图未加载完成）。
        2. 若已有存活 Boss，先将其移除（kill）。
        3. 实例化一个 Enemy 对象，sprite_type 内部设为 'raccoon'，
           传入 is_boss=True 和 boss_phase 参数以启用 Boss 行为，
           并绑定 _on_boss_killed 回调。
        """
        if self._boss_spawn_pos is None:
            return
        # 如果之前有 Boss 存活，先移除（防止重复生成）
        if self.boss and self.boss.alive():
            self.boss.kill()
        self.boss = Enemy(
            'raccoon', self._boss_spawn_pos,
            [self.level.visible_sprites, self.level.combat.attackable_sprites],
            self.level.obstacle_sprites,
            self.level.combat.damage_player,
            self.level.trigger_death_particles,
            self.level.add_exp,
            trigger_exp_particles=lambda enemy_pos, player_pos, exp_amount=0, level=self.level:
                level.trigger_exp_particles(enemy_pos, player_pos, exp_amount),
            pathfinding_grid=self.level.pathfinding_grid,
            tile_size=TILESIZE,
            is_boss=True,           # 启用 Boss 特殊行为（如阶段属性倍率）
            boss_phase=phase,       # 当前阶段编号，影响攻防血等数值
            on_boss_killed=self._on_boss_killed,  # 死亡回调
        )

    def _on_boss_killed(self, death_pos):
        """Boss 死亡回调：计数击杀次数，决定重生下一阶段或触发胜利。

        参数:
            death_pos: Boss 死亡时的像素坐标（可用于粒子特效，但当前未使用）。

        逻辑：
        - 击杀计数 +1，清除当前 Boss 引用。
        - 若击杀次数 >= 3，置胜利标志并返回（不再重生）。
        - 否则计算出下一阶段编号（当前击杀次数 + 1），
          调用 spawn_boss() 在同一位置重生更强 Boss。
        """
        self.boss_kills += 1
        self.boss = None

        if self.boss_kills >= 3:
            # 三阶段全部击杀，触发胜利
            self._trigger_victory = True
            return

        # 在同一固定位置重生下一阶段 Boss
        next_phase = self.boss_kills + 1
        self.spawn_boss(phase=next_phase)


# ── Map Renderer（地图渲染器）──────────────────────────────────────────
class MapRenderer:
    """地图渲染器：绘制全屏世界地图叠加层（按 M 键切换）。

    在游戏画面之上绘制半透明覆盖层，展示：
    - 可通行/障碍物网格（绿色/灰色方块）
    - 敌人位置（红色圆点）
    - Boss 位置（红色闪烁 X 标记 + 红色光圈）
    - 玩家位置（绿色脉冲圆点 + "YOU" 标签）
    - 坐标信息和 Boss 击杀进度（底部状态栏）
    - 图例说明

    该类的逻辑已完全从 Level 主类中抽离，职责单一。
    """

    def __init__(self, level):
        """初始化地图渲染器。

        参数:
            level: Level 主类实例，用于访问寻路网格、玩家、精灵组等。
        """
        self.level = level

    def draw(self):
        """绘制全屏半透明地图覆盖层。

        绘制步骤：
        1. 获取寻路网格(grid)的尺寸，若无网格则直接返回。
        2. 计算每个网格单元格在屏幕上的像素大小(cell_w/cell_h)。
        3. 创建半透明黑色遮罩覆盖全屏。
        4. 遍历网格，用不同颜色绘制可通行(绿色)和障碍物(灰色)方块。
        5. 遍历 attackable_sprites，在敌人位置绘制红色圆点；
           Boss 额外绘制脉冲光圈和红色 X 标记以及 "BOSS" 标签。
        6. 在玩家位置绘制绿色脉冲圆点和 "YOU" 标签。
        7. 底部显示玩家坐标和 Boss 击杀进度信息。
        8. 右上角绘制图例（You / Enemy / BOSS）。
        9. 地图区域外围绘制金色边框。
        """
        level = self.level
        grid = level.pathfinding_grid
        if not grid:
            return
        grid_h = len(grid)
        grid_w = len(grid[0]) if grid_h > 0 else 0
        if grid_w == 0 or grid_h == 0:
            return

        display_surface = level.display_surface
        sw, sh = display_surface.get_size()
        margin = 40
        map_width = sw - margin * 2
        map_height = sh - margin * 2 - 50
        cell_w = map_width / grid_w
        cell_h = map_height / grid_h
        margin_x = margin
        margin_y = margin + 45

        dark = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 200))
        display_surface.blit(dark, (0, 0))

        title_font = pygame.font.Font(None, 36)
        title = title_font.render("WORLD MAP (M to close)", True, (255, 215, 0))
        display_surface.blit(title, (margin_x, margin_y - 40))

        for row in range(grid_h):
            for col in range(grid_w):
                x = margin_x + col * cell_w
                y = margin_y + row * cell_h
                if grid[row][col] == 1:
                    color = (50, 50, 50, 220)
                else:
                    color = (80, 130, 80, 140)
                cell_rect = pygame.Rect(x, y, cell_w + 0.5, cell_h + 0.5)
                pygame.draw.rect(display_surface, color, cell_rect)

        # Draw enemies (boss gets BIG RED X)
        for sprite in level.combat.attackable_sprites:
            if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'enemy':
                ex = int(margin_x + (sprite.rect.centerx / TILESIZE) * cell_w)
                ey = int(margin_y + (sprite.rect.centery / TILESIZE) * cell_h)
                if getattr(sprite, 'is_boss', False):
                    boss_pulse = (pygame.time.get_ticks() // 300) % 2
                    size = 24 if boss_pulse else 18
                    pygame.draw.circle(display_surface, (255, 0, 0, 80), (ex, ey), size + 10)
                    pygame.draw.circle(display_surface, (255, 0, 0, 40), (ex, ey), size + 18)
                    dx = size
                    pygame.draw.line(display_surface, (255, 0, 0), (ex-dx, ey-dx), (ex+dx, ey+dx), 4)
                    pygame.draw.line(display_surface, (255, 0, 0), (ex+dx, ey-dx), (ex-dx, ey+dx), 4)
                    pygame.draw.line(display_surface, (255, 255, 0), (ex-dx, ey-dx), (ex+dx, ey+dx), 2)
                    pygame.draw.line(display_surface, (255, 255, 0), (ex+dx, ey-dx), (ex-dx, ey+dx), 2)
                    label = title_font.render("BOSS", True, (255, 50, 50))
                    lbl_rect = label.get_rect(midbottom=(ex, ey - size - 8))
                    pygame.draw.rect(display_surface, (0, 0, 0, 200), lbl_rect.inflate(10, 6))
                    display_surface.blit(label, lbl_rect)
                else:
                    pygame.draw.circle(display_surface, (255, 0, 0, 80), (ex, ey), 8)
                    pygame.draw.circle(display_surface, (255, 50, 50), (ex, ey), 5)

        # Draw player (GREEN ARROW)
        player = level.player
        px = int(margin_x + (player.rect.centerx / TILESIZE) * cell_w)
        py = int(margin_y + (player.rect.centery / TILESIZE) * cell_h)
        pulse = (pygame.time.get_ticks() // 400) % 2
        psize = 10 if pulse else 8
        pygame.draw.circle(display_surface, (0, 255, 0, 60), (px, py), psize + 8)
        pygame.draw.circle(display_surface, (255, 255, 255), (px, py), psize + 2)
        pygame.draw.circle(display_surface, (0, 255, 0), (px, py), psize)
        you_label = title_font.render("YOU", True, (0, 255, 0))
        you_rect = you_label.get_rect(midbottom=(px, py - psize - 8))
        pygame.draw.rect(display_surface, (0, 0, 0, 200), you_rect.inflate(8, 4))
        display_surface.blit(you_label, you_rect)

        # Info at bottom
        coord_font = pygame.font.Font(None, 22)
        boss_kills = level.boss.boss_kills if level.boss else 0
        info = f"POS: ({int(player.rect.centerx//TILESIZE)}, {int(player.rect.centery//TILESIZE)})  |  Boss: {boss_kills}/3"
        info_text = coord_font.render(info, True, (200, 200, 200))
        display_surface.blit(info_text, (margin_x, margin_y + map_height + 8))

        # Legend
        lx = margin_x + map_width - 150
        ly = margin_y + map_height + 4
        legend_font = pygame.font.Font(None, 18)
        pygame.draw.circle(display_surface, (0, 255, 0), (lx + 6, ly + 8), 5)
        display_surface.blit(legend_font.render("You", True, (200, 200, 200)), (lx + 16, ly))
        pygame.draw.circle(display_surface, (255, 50, 50), (lx + 6, ly + 28), 5)
        display_surface.blit(legend_font.render("Enemy", True, (200, 200, 200)), (lx + 16, ly + 20))
        dx2 = 6
        pygame.draw.line(display_surface, (255, 0, 0), (lx+6-dx2, ly+48-dx2), (lx+6+dx2, ly+48+dx2), 3)
        pygame.draw.line(display_surface, (255, 0, 0), (lx+6+dx2, ly+48-dx2), (lx+6-dx2, ly+48+dx2), 3)
        display_surface.blit(legend_font.render("BOSS", True, (255, 0, 0)), (lx + 16, ly + 40))

        border_rect = pygame.Rect(margin_x, margin_y, map_width, map_height)
        pygame.draw.rect(display_surface, (255, 215, 0), border_rect, 3)


# ── Level（游戏关卡协调者）────────────────────────────────────────────
class Level:
    """游戏关卡协调者：串联所有子系统，驱动每帧的游戏循环。

    职责设计（委托模式）：
    - CombatManager：战斗逻辑（武器/魔法/碰撞/伤害）
    - BossManager：Boss 三阶段生成与胜利触发
    - MapRenderer：全屏地图覆盖层绘制
    - YSortCameraGroup：Y 轴排序 + 摄像机跟随
    - UI：HUD 界面显示
    - Upgrade：升级面板
    - AnimationPlayer / MagicPlayer：粒子特效与魔法动画
    """

    def get_savable_state(self):
        """获取当前关卡可存档的状态字典。

        返回:
            dict: 包含玩家数据、已击败敌人列表、已摧毁草丛列表，
                  用于存档写入。
        """
        return {
            'player': self.player.to_dict(),
            'defeated_enemies': list(self.killed_enemies),
            'destroyed_grass': list(self.destroyed_grass),
        }

    def __init__(self, map_id, player=None, loaded_data=None, player_spawn_pos=None):
        """初始化关卡。

        参数:
            map_id:          地图标识符（用于加载对应的 CSV 地图文件）。
            player:          已有的 Player 实例（跨地图切换时传入），
                             为 None 时由 MapManager 新建。
            loaded_data:     存档数据字典（含 player、defeated_enemies、
                             destroyed_grass），用于恢复游戏状态。
            player_spawn_pos:玩家出生位置像素坐标，跨地图切换时使用。
        """
        # ─── 基础设置 ───
        self.display_surface = pygame.display.get_surface()
        self.game_paused = False    # 升级菜单暂停标志
        self.show_map = False       # 全屏地图叠加层开关

        # ─── 精灵组 ───
        self.visible_sprites = YSortCameraGroup()   # 可见精灵 + Y轴排序 + 摄像机
        self.obstacle_sprites = pygame.sprite.Group()  # 障碍物精灵（阻挡移动）

        # ─── 子管理器 ───
        self.combat = CombatManager(self)       # 战斗管理器
        self.boss = BossManager(self)           # Boss 管理器
        self.map_renderer = MapRenderer(self)   # 地图渲染器

        # ─── 玩家设置 ───
        self.player = player
        if player is not None and player_spawn_pos is not None:
            self._player_spawn_pos = player_spawn_pos
        elif player is None and player_spawn_pos is not None:
            self._player_spawn_pos = player_spawn_pos
        else:
            self._player_spawn_pos = None

        # 委托 MapManager 加载地图（CSV、瓦片、实体、寻路网格）
        MapManager(self, map_id, loaded_data).load()

        # ─── 界面 ───
        self.ui = UI()                  # HUD 界面
        self.upgrade = Upgrade(self.player)  # 升级面板

        # ─── 粒子与魔法动画 ───
        self.animation_player = AnimationPlayer()
        self.magic_player = MagicPlayer(self.animation_player)

        # ─── Boss 背景音乐 ───
        self._boss_music_active = False
        self._boss_bgm_path = get_path('../audio/boss_bgm.ogg')

        # ─── 存档追踪数据 ───
        self.killed_enemies = []    # 已击败的普通敌人列表
        self.destroyed_grass = []   # 已摧毁的草丛列表

    # ── Compatibility Properties（兼容属性）──────────────────────────
    # 这些属性确保 main.py 和 MapManager 仍能以原始属性路径访问数据，
    # 即使内部实现已委托给子管理器对象。

    @property
    def current_attack(self):
        """获取当前武器攻击实例（委托 CombatManager）。"""
        return self.combat.current_attack

    @current_attack.setter
    def current_attack(self, value):
        """设置当前武器攻击实例（委托 CombatManager）。"""
        self.combat.current_attack = value

    @property
    def attack_sprites(self):
        """获取攻击碰撞精灵组（委托 CombatManager）。"""
        return self.combat.attack_sprites

    @property
    def attackable_sprites(self):
        """获取可攻击精灵组（委托 CombatManager）。"""
        return self.combat.attackable_sprites

    @property
    def boss_kills(self):
        """获取 Boss 已击杀次数（委托 BossManager）。"""
        return self.boss.boss_kills

    @property
    def _trigger_victory(self):
        """获取胜利触发标志（委托 BossManager）。"""
        return self.boss._trigger_victory

    @property
    def _boss_spawn_pos(self):
        """获取 Boss 生成位置（委托 BossManager）。"""
        return self.boss._boss_spawn_pos

    @_boss_spawn_pos.setter
    def _boss_spawn_pos(self, value):
        """设置 Boss 生成位置（委托 BossManager）。"""
        self.boss._boss_spawn_pos = value

    # ── Delegated Methods（委托方法，供 MapManager 兼容调用）──────────

    def _spawn_boss(self, phase):
        """生成指定阶段的 Boss（委托 BossManager）。"""
        self.boss.spawn_boss(phase)

    def create_attack(self):
        """创建近战武器攻击（委托 CombatManager）。"""
        self.combat.create_attack()

    def create_magic(self, style, strength, cost):
        """创建魔法攻击（委托 CombatManager）。

        参数:
            style:    魔法类型 'heal' 或 'flame'。
            strength: 魔法强度。
            cost:     法力消耗。
        """
        self.combat.create_magic(style, strength, cost)

    def destroy_attack(self):
        """销毁当前武器攻击（委托 CombatManager）。"""
        self.combat.destroy_attack()

    def player_attack_logic(self):
        """执行玩家攻击碰撞检测逻辑（委托 CombatManager）。"""
        self.combat.player_attack_logic()

    def damage_player(self, amount, attack_type):
        """对玩家造成伤害（委托 CombatManager）。

        参数:
            amount:     伤害数值。
            attack_type:攻击类型（用于粒子特效）。
        """
        self.combat.damage_player(amount, attack_type)

    # ── Particle / EXP Callbacks（粒子特效/经验回调）─────────────────

    def trigger_exp_particles(self, enemy_pos, player_pos, exp_amount=0):
        """在敌人死亡位置生成经验值飘字粒子。

        参数:
            enemy_pos:  敌人死亡时的像素坐标。
            player_pos: 玩家当前位置像素坐标（用于计算经验飘移方向）。
            exp_amount: 获得的经验数值（显示在粒子文字中）。
        """
        self.animation_player.create_exp_particles(
            enemy_pos, player_pos, self.visible_sprites,
            amount=5, exp_amount=exp_amount)

    def _record_enemy_death(self, pos, monster_name):
        """记录敌人死亡位置到存档列表（Boss 除外）。

        参数:
            pos:          死亡位置像素坐标。
            monster_name: 怪物名称字符串，'raccoon'（Boss）不记录，
                          普通敌人才记录。
        """
        if monster_name != 'raccoon':
            self.killed_enemies.append({'x': pos[0], 'y': pos[1]})

    def trigger_death_particles(self, pos, particle_type):
        """在指定位置生成死亡粒子特效，并记录存档数据。

        参数:
            pos:           粒子生成位置像素坐标。
            particle_type: 粒子类型（也作为怪物名称用于存档记录）。
        """
        self.animation_player.create_particles(
            particle_type, pos, self.visible_sprites)
        self._record_enemy_death(pos, particle_type)

    def add_exp(self, amount):
        """向玩家增加经验值。

        参数:
            amount: 增加的经验数值。
        """
        self.player.exp += amount

    # ── UI Toggles（界面切换）─────────────────────────────────────────

    def toggle_menu(self):
        """切换升级菜单的暂停/继续状态。"""
        self.game_paused = not self.game_paused

    def toggle_map(self):
        """切换全屏地图叠加层的显示/隐藏。"""
        self.show_map = not self.show_map

    # ── Boss Music（Boss 背景音乐）────────────────────────────────────

    def _check_boss_music(self):
        """检测玩家是否进入 Boss 警戒范围，切换 Boss 专属背景音乐。

        设计说明（短路优化）：
        - 使用 MusicState 全局状态机：0=普通音乐，1=Boss 音乐已触发。
        - 一旦 MusicState.get() == 1，立即 return（短路），
          避免后续每帧重复计算距离和加载音频文件。
        - 当玩家首次进入 Boss 的 notice_radius 时，将状态设为 1，
          如果玩家不在无敌状态，则停止当前音乐并播放 Boss BGM。
        - 如果玩家处于无敌状态（开局无敌保护），仅设状态标记，
          不实际播放音乐——避免在无敌期间打断普通背景音乐。

        短路优化效果：
          从 O(n) 每帧检测降为 O(1) 单次检测，之后零开销。
        """
        if MusicState.get() == 1:
            return  # Boss 音乐已触发，跳过所有检查（短路）
        boss = self.boss.boss
        if boss and boss.alive():
            boss_vec = pygame.math.Vector2(boss.rect.center)
            player_vec = pygame.math.Vector2(self.player.rect.center)
            dist = (player_vec - boss_vec).magnitude()
            if dist <= boss.notice_radius:
                MusicState.set(1)
                if not self.player.invincible:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(self._boss_bgm_path)
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)

    # ── Main Game Loop（主游戏循环）────────────────────────────────────

    def run(self, dt):
        """每帧执行的游戏主循环。

        参数:
            dt: 上一帧到当前帧的时间差（delta time），用于平滑移动和动画。

        执行顺序：
        1. 绘制可见精灵（摄像机跟随 + Y 轴排序）。
        2. 绘制 HUD 界面（含 Boss 击杀进度）。
        3. 若游戏暂停（升级菜单打开），绘制升级面板。
        4. 若游戏运行中：
           a. 更新所有精灵状态（玩家移动、动画等）。
           b. 更新敌人 AI 行为（追踪玩家）。
           c. 执行玩家攻击碰撞检测。
           d. 检测 Boss 音乐触发条件。
        5. 若地图叠加层打开，绘制全屏地图。
        """
        # update and draw the game
        self.visible_sprites.custom_draw(self.player)
        self.ui.display(self.player,
                        boss_kills=self.boss.boss_kills,
                        boss_sprite=self.boss.boss)

        if self.game_paused:
            self.upgrade.display()
        else:
            self.visible_sprites.update(dt)
            self.visible_sprites.enemy_update(self.player)
            self.player_attack_logic()
            self._check_boss_music()

        # Draw map overlay on top if active
        if self.show_map:
            self.map_renderer.draw()


# ── Y-Sort Camera Group（Y轴排序摄像机组）─────────────────────────────
class YSortCameraGroup(pygame.sprite.Group):
    """Y轴排序精灵组 + 摄像机跟随。

    继承自 pygame.sprite.Group，在绘制精灵时会：
    - 根据玩家位置计算摄像机偏移量（居中跟随）。
    - 按精灵的 rect.centery（Y 坐标）升序排列绘制顺序，
      实现"下方物体覆盖上方"的 2.5D 透视效果。
    - 先绘制地面底图，再绘制排序后的精灵。
    - 提供 enemy_update() 用于批量更新敌人的 AI 行为。
    """

    def __init__(self):
        """初始化 Y 轴排序摄像机组。

        设置显示表面引用、屏幕半宽/半高（用于居中偏移计算）、
        摄像机偏移向量，并加载地面底图图片。
        """
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

        floor_path = get_path('../graphics/tilemap/ground.png')
        self.floor_surf = pygame.image.load(floor_path).convert()
        self.floor_rect = self.floor_surf.get_rect(topleft=(0, 0))

    def custom_draw(self, player):
        """以玩家为中心绘制所有可见精灵（带 Y 轴排序）。

        参数:
            player: 玩家精灵对象，其位置决定摄像机偏移量。

        绘制流程：
        1. 计算摄像机偏移量，使玩家始终位于屏幕中央。
        2. 在偏移后的位置绘制地面底图。
        3. 将所有精灵按 rect.centery 排序（Y 值大的靠后绘制），
           然后逐一绘制到屏幕上。
        """
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        floor_offset_pos = self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf, floor_offset_pos)

        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_rect = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_rect)

    def enemy_update(self, player):
        """批量更新所有敌人的 AI 行为（追踪玩家等）。

        参数:
            player: 玩家精灵对象，传入每个敌人生成目标信息。

        过滤出 sprite_type == 'enemy' 的精灵，逐一调用
        其 enemy_update() 方法更新 AI 状态。
        """
        enemy_sprites = [sprite for sprite in self.sprites() if hasattr(
            sprite, 'sprite_type') and sprite.sprite_type == 'enemy']

        for enemy in enemy_sprites:
            enemy.enemy_update(player)
