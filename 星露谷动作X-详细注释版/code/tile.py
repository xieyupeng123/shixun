# -*- coding: utf-8 -*-
"""
tile.py — 瓦片精灵（Tile）

定义 Tile 类，作为地图中所有静态元素的精灵基类。
包括地面、墙壁、树木、建筑物、装饰物等所有非角色地图对象。

根据不同 sprite_type，自动选择碰撞箱偏移和图像定位方式。
"""

import pygame
from settings import TILESIZE, HITBOX_OFFSET


class Tile(pygame.sprite.Sprite):
    """
    瓦片精灵类，表示地图上的一个静态元素。

    三种主要瓦片类型（由 sprite_type 区分）：
        - 'object'：大型物体（如树木、房屋、箱子），图像比标准 TILE SIZE 大，
                    需要向上偏移一个 TILESIZE 来正确定位
        - 'grass'：草地元素，碰撞箱较小允许玩家穿过
        - 'invisible'：不可见碰撞墙（用于地图边界和阻挡）

    碰撞箱（hitbox）通过 HITBOX_OFFSET 配置进行垂直方向的微调，
    使实际碰撞区域比图像显示区域更小，提升操作手感。
    """

    def __init__(self, pos, groups, sprite_type, surface=None):
        """
        初始化瓦片精灵。

        参数:
            pos (tuple): 瓦片在地图上的像素坐标 (x, y)（左上角定位点）
            groups (list[pygame.sprite.Group]): 所有要加入的精灵组列表，
                通常包括 visible_sprites、obstacle_sprites 等
            sprite_type (str): 瓦片类型标识，支持 'object'、'grass'、'invisible' 等，
                决定了图像定位方式和碰撞箱偏移量
            surface (pygame.Surface, optional): 瓦片图像表面。
                若不提供，则创建一个 TILESIZE × TILESIZE 的空白表面
        """
        super().__init__(groups)
        self.sprite_type = sprite_type  # 瓦片类型标识

        # 从 settings 中读取当前类型对应的碰撞箱垂直偏移量
        y_offset = HITBOX_OFFSET[sprite_type]

        # 设置图像表面：若提供了 surface 则使用，否则创建一个空白表面
        self.image = surface if surface is not None else pygame.Surface((TILESIZE, TILESIZE))

        if sprite_type == 'object':
            # 大型物体（如树木、建筑）的图像通常比标准 64×64 大，
            # 其定位点需要向上偏移一个 TILESIZE，使底部与地面平齐
            self.rect = self.image.get_rect(
                topleft=(pos[0], pos[1] - TILESIZE))
        else:
            # 普通瓦片直接以 pos 为左上角定位
            self.rect = self.image.get_rect(topleft=pos)

        # 碰撞箱：在图像矩形基础上进行调整
        # 水平收缩 10 像素（两侧各 5 像素），垂直方向按 HITBOX_OFFSET 配置偏移
        # 使实际碰撞区域比视觉外观小，避免玩家被"空气墙"卡住
        self.hitbox = self.rect.inflate(-10, y_offset)
