import pygame
from settings import UI_FONT, UI_FONT_SIZE, TEXT_COLOR_SELECTED, TEXT_COLOR, BAR_COLOR_SELECTED, BAR_COLOR, UPGRADE_BG_COLOR_SELECTED, UI_BG_COLOR, UI_BORDER_COLOR


class Upgrade:
    """
    升级菜单类 — 管理五维属性的升降级界面与交互逻辑。

    玩家完成冒险后可通过此菜单消耗经验值（EXP）来提升五维属性，
    也可降级已升级的属性来回收部分经验值。

    属性列表（来自 player.stats）：
      'health'  : 生命值
      'energy'  : 能量值
      'attack'  : 攻击力
      'magic'   : 魔法强度
      'speed'   : 移动速度
    """

    def __init__(self, player):
        """
        初始化升级菜单。

        参数：
          player : 玩家对象，用于读取/修改 stats、exp、max_stats、upgrade_cost

        初始化内容：
          - 计算每个属性列的宽度（屏幕宽度 ÷ (属性数+1)）
          - 计算属性列的高度（屏幕高度 × 0.8）
          - 为每个属性创建 Item 对象
          - 初始化选中索引为 0（第一个属性）
          - 设置键盘输入冷却（300ms），防止一次按键触发多次
        """
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = player
        self.attributes_len = len(player.stats)
        self.attributes_names = list(player.stats.keys())
        self.max_values = list(player.max_stats.values())
        self.font = pygame.font.Font(UI_FONT, UI_FONT_SIZE)

        # item creation
        self.width = self.display_surface.get_size()[
            0] // (self.attributes_len + 1)
        self.height = self.display_surface.get_size()[1] * 0.8
        self.create_items()

        # selection system
        self.selection_index = 0
        self.selection_time = None
        self.can_move = True

    def input(self):
        """
        处理键盘输入，控制选中项的切换和升降级操作。

        按键映射：
          ←/→   : 在五维属性之间左右切换选中项
          ↑      : 升级当前选中属性（触发 Item.trigger）
          ↓      : 降级当前选中属性（触发 Item.downgrade）

        每次操作后设置 can_move = False 并记录时间，
        通过 selection_cooldown 防止连续触发。
        """
        keys = pygame.key.get_pressed()
        if self.can_move:
            if keys[pygame.K_RIGHT] and self.selection_index < self.attributes_len - 1:
                self.selection_index += 1
                self.can_move = False
                self.selection_time = pygame.time.get_ticks()
            elif keys[pygame.K_LEFT] and self.selection_index >= 1:
                self.selection_index -= 1
                self.can_move = False
                self.selection_time = pygame.time.get_ticks()

            if keys[pygame.K_UP]:
                self.can_move = False
                self.selection_time = pygame.time.get_ticks()
                self.items[self.selection_index].trigger(self.player)

            if keys[pygame.K_DOWN]:
                self.can_move = False
                self.selection_time = pygame.time.get_ticks()
                self.items[self.selection_index].downgrade(self.player)

    def selection_cooldown(self):
        """
        键盘输入冷却机制。

        每次操作后锁定输入 300ms，避免按住按键时过快切换。
        冷却结束后将 can_move 恢复为 True。
        """
        if not self.can_move and self.selection_time is not None:
            current_time = pygame.time.get_ticks()
            if current_time - self.selection_time >= 300:
                self.can_move = True

    def create_items(self):
        """
        创建五维属性对应的 Item 对象列表。

        布局计算：
          - 每个属性的宽度 = 屏幕宽度 ÷ (属性数 + 1)
          - 水平位置 = 属性索引 × 等分间隔 + 居中对齐偏移
          - 垂直位置 = 屏幕高度的 10%（顶部留白）
          - 高度 = 屏幕高度的 80%（预留底部空间显示数值和消耗）
        """
        self.items = []

        for index in range(self.attributes_len):
            # horizontal pos
            full_width = self.display_surface.get_size()[0]
            increment = full_width // self.attributes_len
            left = (index * increment) + (increment - self.width) // 2

            # vertical pos
            top = self.display_surface.get_size()[1] * 0.1

            # create the object
            item = Item(left, top, self.width, self.height, index, self.font)
            self.items.append(item)

    def display(self):
        """
        每帧调用，绘制整个升级菜单。

        步骤：
          1. 处理键盘输入（切换/升降级）
          2. 检查输入冷却
          3. 遍历所有 Item，获取每个属性的名称、当前值、最大值和升级消耗
          4. 调用每个 Item 的 display 方法绘制到屏幕
        """
        self.input()
        self.selection_cooldown()

        for index, item in enumerate(self.items):
            name = self.attributes_names[index]
            value = self.player.get_value_by_index(index)
            max_value = self.max_values[index]
            cost = self.player.get_cost_by_index(index)
            item.display(self.display_surface, self.selection_index,
                         name, value, max_value, cost)


class Item:
    """
    单个属性列的 UI 组件，负责绘制属性名称、数值条和升级消耗。

    每个 Item 对应五维（health/energy/attack/magic/speed）中的一个属性。
    """

    def __init__(self, left, t, w, h, index, font):
        """
        参数：
          left  : 属性列左侧 X 坐标
          t     : 属性列顶部 Y 坐标
          w     : 属性列宽度
          h     : 属性列高度
          index : 属性索引（对应 player.stats 的键顺序）
          font  : 文字字体
        """
        self.rect = pygame.Rect(left, t, w, h)
        self.index = index
        self.font = font

    def display_names(self, surface, name, cost, selected):
        """
        在属性列顶部绘制属性名称，底部绘制升级消耗经验值。

        参数：
          surface : 目标绘制表面
          name    : 属性名称字符串（如 'health'）
          cost    : 下一次升级所需的经验值
          selected: 当前属性是否被选中（影响文字颜色）
        """
        color = TEXT_COLOR_SELECTED if selected else TEXT_COLOR

        # title — 属性名称，位于列上方
        title_surf = self.font.render(name, False, color)
        title_rect = title_surf.get_rect(
            midtop=self.rect.midtop + pygame.math.Vector2(0, 20))

        # cost — 升级消耗，位于列下方
        cost_surf = self.font.render(f'{int(cost)}', False, color)
        cost_rect = cost_surf.get_rect(
            midbottom=self.rect.midbottom - pygame.math.Vector2(0, 20))

        # draw
        surface.blit(title_surf, title_rect)
        surface.blit(cost_surf, cost_rect)

    def display_bar(self, surface, value, max_value, selected):
        """
        绘制属性值的竖向条形图。

        参数：
          surface  : 目标绘制表面
          value    : 当前属性值
          max_value: 属性最大值（用于计算填充比例）
          selected : 是否选中（控制颜色）

        绘制方式：
          - 用一条垂直线表示满值范围（从 top 到底部）
          - 用一个小矩形表示当前值（从底部向上按比例填充）
          - 视觉上类似"温度计"效果
        """
        # 计算垂直线起点（上）和终点（下）
        top = self.rect.midtop + pygame.math.Vector2(0, 60)
        bottom = self.rect.midbottom - pygame.math.Vector2(0, 60)
        color = BAR_COLOR_SELECTED if selected else BAR_COLOR

        # 计算当前值对应的像素高度，从底部向上绘制
        full_height = bottom[1] - top[1]
        relative_num = (value / max_value) * full_height
        value_rect = pygame.Rect(top[0] - 15, bottom[1] - relative_num, 30, 10)

        # 绘制垂直线（满值范围）和填充矩形（当前值）
        pygame.draw.line(surface, color, top, bottom, 5)
        pygame.draw.rect(surface, color, value_rect)

    def trigger(self, player):
        """
        执行属性升级（按 ↑ 键触发）。

        升级逻辑（三步走）：
          1. 条件检查：经验值足够 && 当前值 < 最大值
          2. 扣减经验：player.exp -= 升级消耗
          3. 属性增长：当前值 *= 1.2（保留整数类型的整型特性）
          4. 消耗递增：下次升级成本 *= 1.4（指数增长）
          5. 越界保护：若超过最大值则 clamp 到最大值

        每次升级的成本和属性值都按固定倍率增长，
        形成"越升越贵"的曲线，鼓励玩家在五维间平衡投入。
        """
        upgrade_attribute = list(player.stats.keys())[self.index]
        if player.exp >= player.upgrade_cost[upgrade_attribute] and player.stats[upgrade_attribute] < player.max_stats[upgrade_attribute]:
            player.exp -= player.upgrade_cost[upgrade_attribute]
            # 保留整数类型的整型特性，浮点属性使用浮点运算
            new_val = player.stats[upgrade_attribute] * 1.2
            player.stats[upgrade_attribute] = int(new_val) if isinstance(player.stats[upgrade_attribute], int) else new_val
            player.upgrade_cost[upgrade_attribute] = int(player.upgrade_cost[upgrade_attribute] * 1.4)

        if player.stats[upgrade_attribute] > player.max_stats[upgrade_attribute]:
            player.stats[upgrade_attribute] = player.max_stats[upgrade_attribute]

    def downgrade(self, player):
        """
        执行属性降级 / 退点（按 ↓ 键触发），回收部分经验。

        降级逻辑：
          1. 条件检查：当前值 > 基础值（PLAYER_BASE_STATS），仅在已升级时才可降级
          2. 经验退款：退还上一次升级的成本（成本 / 1.4，反向计算）
          3. 属性回流：当前值 /= 1.2（反向计算）
          4. 成本回退：升级成本 /= 1.4（反向计算）
          5. 越界保护：若低于基础值则 clamp 到基础值，并重置成本为基础成本

        注意：
          降级与升级的倍率完全对称（×1.2 → ÷1.2, ×1.4 → ÷1.4），
          但降级的数量级倒退可能存在小误差，本实现已做取整处理。
        """
        upgrade_attribute = list(player.stats.keys())[self.index]
        from settings import PLAYER_BASE_STATS, PLAYER_BASE_COSTS
        if player.stats[upgrade_attribute] > PLAYER_BASE_STATS[upgrade_attribute]:
            # Refund the previous upgrade cost
            refund = int(player.upgrade_cost[upgrade_attribute] / 1.4)
            player.exp += refund
            new_val = player.stats[upgrade_attribute] / 1.2
            player.stats[upgrade_attribute] = int(new_val) if isinstance(PLAYER_BASE_STATS[upgrade_attribute], int) else new_val
            player.upgrade_cost[upgrade_attribute] = int(player.upgrade_cost[upgrade_attribute] / 1.4)
            # Clamp to base
            if player.stats[upgrade_attribute] < PLAYER_BASE_STATS[upgrade_attribute]:
                player.stats[upgrade_attribute] = PLAYER_BASE_STATS[upgrade_attribute]
                player.upgrade_cost[upgrade_attribute] = PLAYER_BASE_COSTS[upgrade_attribute]

    def display(self, surface, selection_num, name, value, max_value, cost):
        """
        绘制整个属性列（背景 + 名称 + 数值条 + 消耗）。

        参数：
          surface       : 目标绘制表面
          selection_num : 当前选中的属性索引（由 Upgrade 传递）
          name          : 属性名称
          value         : 当前属性值
          max_value     : 属性最大值
          cost          : 升级消耗经验值

        选中效果：
          - 背景色变为 UPGRADE_BG_COLOR_SELECTED
          - 名称和消耗文字变色
          - 数值条颜色变色
        """
        if self.index == selection_num:
            pygame.draw.rect(surface, UPGRADE_BG_COLOR_SELECTED, self.rect)
        else:
            pygame.draw.rect(surface, UI_BG_COLOR, self.rect)
        pygame.draw.rect(surface, UI_BORDER_COLOR, self.rect, 4)

        self.display_names(surface, name, cost, self.index == selection_num)
        self.display_bar(surface, value, max_value,
                         self.index == selection_num)
