"""
weapon —— 武器攻击判定精灵模块

本模块定义了 Weapon 类，是一个一次性 Sprite 对象。
当玩家发起近战攻击时，由上层（create_attack 回调）在当前帧创建该精灵，
在玩家面前生成一个带有武器图像的判定区域，持续数帧后自动销毁。
"""

import pygame
from support import get_path


class Weapon(pygame.sprite.Sprite):
    """Weapon —— 武器攻击判定精灵

    当玩家按下鼠标左键时创建，表示一次近战攻击的判定区域。
    生命周期很短（通常 1~3 帧），由上层系统的销毁机制（destroy_attack 回调）
    在攻击冷却结束后移除。

    主要功能：
      - 根据玩家朝向（direction）将武器图像放置在玩家周围的正确位置
      - 与 Enemy 精灵产生碰撞时触发伤害判定（由上层碰撞系统处理）
      - 不同武器使用不同的图像资源（由 weapon_data 中的武器名称决定路径）

    位置计算：
      武器图像紧贴玩家身体放置，方向不同偏移量也不同：
        - 右：武器左侧边对齐玩家右侧边 + Y 向下偏移 16 像素
        - 左：武器右侧边对齐玩家左侧边 + Y 向下偏移 16 像素
        - 下：武器顶部对齐玩家底部 + X 向左偏移 10 像素
        - 上：武器底部对齐玩家顶部 + X 向左偏移 10 像素
    """

    def __init__(self, player, groups):
        """创建武器攻击判定精灵

        根据玩家的当前朝向和武器类型，加载对应图像并计算放置位置。
        创建后将自动加入到指定的精灵组中（通常包含 attack_sprites）。

        参数:
            player (Player): 玩家对象引用，用于获取位置、朝向和武器类型
            groups (list[pygame.sprite.Group]): 该精灵要加入的精灵组列表。
                通常包含一个专门用于攻击判定的精灵组，供碰撞系统检测。
        """
        super().__init__(groups)
        self.sprite_type = 'weapon'  # 精灵类型标签，碰撞检测时用于识别

        # 从玩家状态字符串中提取方向部分
        # player.status 的格式为 'down' / 'down_idle' / 'down_attack'
        # 通过 split('_')[0] 只取方向部分（去掉 '_idle'、'_attack' 等后缀）
        direction = player.status.split('_')[0]

        # ── 加载武器图像 ──
        # 路径格式：../graphics/weapons/{武器名称}/{方向}.png
        # 例如：../graphics/weapons/sword/right.png
        full_path = get_path(
            f'../graphics/weapons/{player.weapon}/{direction}.png')
        self.image = pygame.image.load(full_path).convert_alpha()

        # ── 根据攻击方向计算武器图像的放置位置 ──
        # 武器的 rect 位置相对于玩家的 rect，偏移量使武器看起来像是
        # 从玩家手中挥出，而非出现在玩家身体内部。
        #
        # 四种方向的偏移策略：
        if direction == 'right':
            # 武器在玩家右侧：武器图像左边缘对齐玩家右边缘
            # Vector2(0, 16) 表示 Y 方向向下偏移 16 像素（让武器看起来在腰部高度）
            self.rect = self.image.get_rect(
                midleft=player.rect.midright + pygame.math.Vector2(0, 16))
        elif direction == 'left':
            # 武器在玩家左侧：武器图像右边缘对齐玩家左边缘
            self.rect = self.image.get_rect(
                midright=player.rect.midleft + pygame.math.Vector2(0, 16))
        elif direction == 'down':
            # 武器在玩家下方：武器图像顶部对齐玩家底部
            # Vector2(-10, 0) 表示 X 方向向左偏移 10 像素（居中调整）
            self.rect = self.image.get_rect(
                midtop=player.rect.midbottom + pygame.math.Vector2(-10, 0))
        else:  # direction == 'up'
            # 武器在玩家上方：武器图像底部对齐玩家顶部
            self.rect = self.image.get_rect(
                midbottom=player.rect.midtop + pygame.math.Vector2(-10, 0))
