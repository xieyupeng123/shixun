import pygame
from settings import UI_FONT, UI_FONT_SIZE, HEALTH_BAR_WIDTH, BAR_HEIGHT, ENERGY_BAR_WIDTH, weapon_data, magic_data, UI_BG_COLOR, UI_BORDER_COLOR, TEXT_COLOR, UI_BORDER_COLOR_ACTIVE, HEALTH_COLOR, ENERGY_COLOR, ITEM_BOX_SIZE, monster_data, BOSS_PHASE_DATA
from resource_manager import ResourceManager


class UI:
    """
    HUD（Heads-Up Display）渲染类。

    负责在游戏画面上叠加显示：
      - 血条与能量条（左上角）
      - 经验值（右下角）
      - 当前武器/魔法图标（左下角）
      - 无敌状态倒计时 / 冷却计时（顶部居中）
      - Boss 阶段、血量、击杀进度（顶部区域）

    所有贴图资源通过 ResourceManager 缓存获取，避免重复加载。
    """

    def __init__(self):
        """
        初始化 UI：
          - 获取主显示表面引用
          - 从 ResourceManager 获取字体
          - 创建血条/能量条的矩形区域
          - 预加载所有武器和魔法的图标贴图列表
        """
        res = ResourceManager.instance()

        # general
        self.display_surface = pygame.display.get_surface()
        self.font = res.get_font(UI_FONT, UI_FONT_SIZE)

        # bar setup
        self.health_bar_rect = pygame.Rect(
            10, 10, HEALTH_BAR_WIDTH, BAR_HEIGHT)
        self.energy_bar_rect = pygame.Rect(
            10, 34, ENERGY_BAR_WIDTH, BAR_HEIGHT)

        # convert weapon dictionary (cached via ResourceManager)
        self.weapon_graphics = []
        for weapon in weapon_data.values():
            path = weapon['graphic']
            weapon_surf = res.get_image(path)
            self.weapon_graphics.append(weapon_surf)

        # convert magic dictionary (cached via ResourceManager)
        self.magic_graphics = []
        for magic in magic_data.values():
            path = magic['graphic']
            magic_surf = res.get_image(path)
            self.magic_graphics.append(magic_surf)

    def show_bar(self, current, max_amount, bg_rect, color):
        """
        绘制单条属性条（血条或能量条）。

        参数：
          current    : 当前值（整数或浮点数）
          max_amount : 最大值（用于计算填充比例）
          bg_rect    : 属性条所在矩形区域 (pygame.Rect)
          color      : 填充颜色（RGB 元组）

        绘制流程：
          1. 先用 UI_BG_COLOR 绘制背景条
          2. 计算 current / max 比率并转换为像素宽度
          3. 用指定颜色绘制实际填充部分
          4. 用 UI_BORDER_COLOR 绘制外边框（3px 线宽）
        """
        # 绘制背景
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)

        # 将数值转换为像素宽度
        ratio = current / max(max_amount, 1)
        current_width = bg_rect.width * ratio
        current_rect = bg_rect.copy()
        current_rect.width = current_width

        # 绘制填充条与边框
        pygame.draw.rect(self.display_surface, color, current_rect)
        pygame.draw.rect(self.display_surface,
                         UI_BORDER_COLOR, bg_rect, 3)

    def show_exp(self, exp):
        """
        在屏幕右下角绘制经验值文字。

        参数：
          exp : 玩家当前经验值（浮点数，显示时将取整显示）

        绘制流程：
          1. 渲染文本，定位至右下角（留 20px 边距）
          2. 在文字背景绘制半透明填充矩形
          3. 绘制边框
        """
        text_surf = self.font.render(str(int(exp)), False, TEXT_COLOR)
        x = self.display_surface.get_size()[0] - 20
        y = self.display_surface.get_size()[1] - 20
        text_rect = text_surf.get_rect(bottomright=(x, y))

        pygame.draw.rect(self.display_surface, UI_BG_COLOR,
                         text_rect.inflate(20, 20))
        self.display_surface.blit(text_surf, text_rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR,
                         text_rect.inflate(20, 20), 3)

    def selection_box(self, left, top, has_switched):
        """
        绘制武器/魔法选择框。

        参数：
          left        : 选择框左上角 X 坐标
          top         : 选择框左上角 Y 坐标
          has_switched: 是否处于"刚切换"状态（此状态下边框用高亮色）

        返回：
          pygame.Rect — 用于后续绘制图标时的定位参考
        """
        bg_rect = pygame.Rect(left, top, ITEM_BOX_SIZE, ITEM_BOX_SIZE)
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)

        if has_switched:
            pygame.draw.rect(self.display_surface,
                             UI_BORDER_COLOR_ACTIVE, bg_rect, 3)
        else:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)
        return bg_rect

    def weapon_overlay(self, weapon_index, has_switched):
        """
        在屏幕左下角绘制当前武器的图标覆盖层。

        参数：
          weapon_index : 当前武器的索引（用于从 weapon_graphics 列表中选取）
          has_switched : 是否刚切换武器（控制边框高亮色）

        步骤：
          1. 调用 selection_box 绘制选择框并获取其 Rect
          2. 从预加载的 weapon_graphics 中取出对应武器图标
          3. 将图标居中对齐在选择框内并绘制
        """
        bg_rect = self.selection_box(10, 630, has_switched)
        weapon_surf = self.weapon_graphics[weapon_index]
        weapon_rect = weapon_surf.get_rect(center=bg_rect.center)

        self.display_surface.blit(weapon_surf, weapon_rect)

    def magic_overlay(self, magic_index, has_switched):
        """
        在屏幕左下角（武器图标右侧）绘制当前魔法的图标覆盖层。

        参数：
          magic_index  : 当前魔法的索引（用于从 magic_graphics 列表中选取）
          has_switched : 是否刚切换魔法（控制边框高亮色）

        与 weapon_overlay 布局位置不同，magic 位于武器图标右侧偏下。
        """
        bg_rect = self.selection_box(80, 635, has_switched)
        magic_surf = self.magic_graphics[magic_index]
        magic_rect = magic_surf.get_rect(center=bg_rect.center)

        self.display_surface.blit(magic_surf, magic_rect)

    def show_invincible_status(self, player):
        """
        在屏幕顶部中央显示无敌（INVINCIBLE）状态指示器。

        三种状态（由 player.get_invincible_status() 返回）：
          - ('active', remaining, 0)    : 无敌激活中
              - 金色文字 "INVINCIBLE  X.Xs"（显示剩余秒数）
              - 金色边框，黑色半透明背景
          - ('cooldown', 0, cd_remaining): 冷却中
              - 灰色文字 "INVINCIBLE CD: M:SS"（显示分：秒）
              - 灰色边框，黑色半透明背景
          - ('ready', 0, 0)             : 无显示（冷却结束，可再次使用）

        参数：
          player : 玩家对象，通过 get_invincible_status() 查询状态
        """
        state, remaining, cd_remaining = player.get_invincible_status()
        sw = self.display_surface.get_size()[0]

        if state == 'active':
            # 无敌激活状态 — 金色文字 + 倒计时秒数
            inv_font = ResourceManager.instance().get_font(UI_FONT, 28)
            text = f"INVINCIBLE  {remaining:.1f}s"
            text_surf = inv_font.render(text, False, (255, 215, 0))
            text_rect = text_surf.get_rect(midtop=(sw // 2, 10))
            bg_rect = text_rect.inflate(30, 10)
            pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect)
            pygame.draw.rect(self.display_surface, (255, 215, 0), bg_rect, 2)
            self.display_surface.blit(text_surf, text_rect)

        elif state == 'cooldown':
            # 冷却状态 — 灰色文字 + 分：秒格式冷却时间
            cd_font = ResourceManager.instance().get_font(UI_FONT, 22)
            mins = int(cd_remaining // 60)
            secs = int(cd_remaining % 60)
            text = f"INVINCIBLE CD: {mins}:{secs:02d}"
            text_surf = cd_font.render(text, False, (150, 150, 150))
            text_rect = text_surf.get_rect(midtop=(sw // 2, 10))
            bg_rect = text_rect.inflate(30, 10)
            pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect)
            pygame.draw.rect(self.display_surface, (100, 100, 100), bg_rect, 2)
            self.display_surface.blit(text_surf, text_rect)

    def show_boss_status(self, boss_kills):
        """
        在屏幕右上角显示 Boss 击杀进度 "BOSS X/3"。

        参数：
          boss_kills : 已击杀 Boss 的次数（0~3）

        阶段颜色映射：
          击杀 0 次 → 不显示
          击杀 1 次（Phase 2）→ 白色
          击杀 2 次（Phase 3）→ 紫色
          击杀 3 次（最终）  → 红色
        """
        if boss_kills <= 0:
            return
        boss_font = ResourceManager.instance().get_font(UI_FONT, 22)
        phase_colors = {1: (255, 255, 255), 2: (180, 80, 220), 3: (255, 40, 40)}
        color = phase_colors.get(boss_kills + 1, (255, 255, 255))
        text = f"BOSS {boss_kills}/3"
        text_surf = boss_font.render(text, False, color)
        x = self.display_surface.get_size()[0] - text_surf.get_width() - 20
        text_rect = text_surf.get_rect(topleft=(x, 12))
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(self.display_surface, color, bg_rect, 2)
        self.display_surface.blit(text_surf, text_rect)

    def show_boss_phase_hud(self, boss_sprite):
        """
        在屏幕顶部中央显示当前 Boss 的阶段名称。

        参数：
          boss_sprite : Boss 精灵对象（pygame.sprite.Sprite），若不存在或已死亡则不显示

        阶段名称与颜色：
          Phase 1 — Normal（正常） → 白色
          Phase 2 — Enraged（狂暴）→ 浅红色
          Phase 3 — Final（最终）  → 紫色
        """
        if not boss_sprite or not boss_sprite.alive():
            return
        phase = getattr(boss_sprite, 'boss_phase', 1)
        phase_names = {1: 'Phase 1 - Normal', 2: 'Phase 2 - Enraged', 3: 'Phase 3 - Final'}
        phase_colors = {1: (255, 255, 255), 2: (255, 150, 150), 3: (200, 100, 255)}
        hud_font = ResourceManager.instance().get_font(UI_FONT, 22)
        text = f"BOSS: {phase_names.get(phase, '?')}"
        text_surf = hud_font.render(text, False, phase_colors.get(phase, (255, 255, 255)))
        text_rect = text_surf.get_rect(midtop=(self.display_surface.get_size()[0] // 2, 40))
        bg_rect = text_rect.inflate(20, 6)
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect)
        self.display_surface.blit(text_surf, text_rect)

    def show_boss_health_bar(self, boss_sprite):
        """
        在屏幕顶部（阶段文字下方）绘制 Boss 血条。

        参数：
          boss_sprite : Boss 精灵对象，若不存在或已死亡则不显示

        血条特征：
          - 宽度 300px，高度 18px
          - 根据 Boss 当前阶段使用不同颜色：
            Phase 1 → 深红
            Phase 2 → 亮红
            Phase 3 → 紫色
          - 中心显示 "当前HP / 最大HP" 文字
          - 最大 HP 由 monster_data['raccoon']['health'] * 阶段倍率计算
        """
        if not boss_sprite or not boss_sprite.alive():
            return
        phase = getattr(boss_sprite, 'boss_phase', 1)
        max_hp = int(monster_data['raccoon']['health'] * BOSS_PHASE_DATA[phase]['stat_mult'])
        current_hp = max(0, boss_sprite.health)
        sw = self.display_surface.get_size()[0]

        # Bar dimensions
        bar_w = 300
        bar_h = 18
        bar_x = (sw - bar_w) // 2
        bar_y = 70

        # Background
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180),
                         pygame.Rect(bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))

        # Health fill
        ratio = current_hp / max_hp if max_hp > 0 else 0
        fill_w = int(bar_w * ratio)
        phase_bar_colors = {1: (200, 50, 50), 2: (255, 120, 120), 3: (180, 80, 220)}
        bar_color = phase_bar_colors.get(phase, (200, 50, 50))
        pygame.draw.rect(self.display_surface, bar_color,
                         pygame.Rect(bar_x, bar_y, fill_w, bar_h))

        # Border
        pygame.draw.rect(self.display_surface, (255, 255, 255),
                         pygame.Rect(bar_x, bar_y, bar_w, bar_h), 2)

        # HP text
        hp_font = ResourceManager.instance().get_font(UI_FONT, 16)
        hp_text = f"{current_hp} / {max_hp}"
        hp_surf = hp_font.render(hp_text, False, (255, 255, 255))
        hp_rect = hp_surf.get_rect(center=(sw // 2, bar_y + bar_h // 2))
        self.display_surface.blit(hp_surf, hp_rect)

    def display(self, player, boss_kills=0, boss_sprite=None):
        """
        主绘制入口，每帧调用一次，渲染所有 HUD 元素。

        绘制顺序（从底部到顶部叠加）：
          1. 血条（左上角）
          2. 能量条（左上角，血条下方）
          3. 经验值（右下角）
          4. 武器图标（左下角）
          5. 魔法图标（左下角）
          6. 无敌状态倒计时 / 冷却指示器（顶部居中）
          7. Boss 击杀进度（右上角）
          8. Boss 阶段名称（顶部居中）
          9. Boss 血条（阶段名称下方）

        参数：
          player      : 玩家对象，读取 health / energy / exp / weapon_index 等属性
          boss_kills  : 已击杀 Boss 次数（默认 0）
          boss_sprite : Boss 精灵引用（默认 None，不显示 Boss 相关 UI）
        """
        self.show_bar(
            player.health, player.stats['health'], self.health_bar_rect, HEALTH_COLOR)
        self.show_bar(
            player.energy, player.stats['energy'], self.energy_bar_rect, ENERGY_COLOR)

        self.show_exp(player.exp)

        self.weapon_overlay(player.weapon_index, not player.can_switch_weapon)
        self.magic_overlay(player.magic_index, not player.can_switch_magic)

        # Invincible state indicator
        self.show_invincible_status(player)

        # Boss indicators
        self.show_boss_status(boss_kills)
        self.show_boss_phase_hud(boss_sprite)
        self.show_boss_health_bar(boss_sprite)
