"""
地图加载与世界几何构建模块。

将地图相关的加载逻辑从 level.py 中抽离，使地图管理职责独立。
核心功能：CSV 地图解析、瓦片放置、水域自动检测、寻路网格构建、
玩家/Boss/敌人生成、存档恢复。
"""
import pygame
import os
from settings import TILESIZE
from tile import Tile
from player import Player
from enemy import Enemy
from support import get_path, import_csv_layout, import_folder
from random import choice
from constants import (
    ENTITY_PLAYER_SPAWN, ENTITY_BOSS_SPAWN,
    ENTITY_MONSTER_MAP,
    LAYER_BOUNDARY, LAYER_GRASS, LAYER_OBJECT, LAYER_ENTITIES,
    SPRITE_GRASS, SPRITE_OBJECT, SPRITE_INVISIBLE,
)
from pathfinding_utils import build_grid, pos_to_grid, grid_to_pos

class MapManager:
    """地图管理器：负责 CSV 地图加载、瓦片放置、水域检测、
    寻路网格构建和实体生成。

    设计说明：
    - 每一层地图分别存储在不同的 CSV 文件中（FloorBlocks/Grass/Objects/Entities）。
    - 加载时按层解析，为每个非空格创建对应的 Tile 或 Entity。
    - 水域检测通过分析 ground.png 底图的像素颜色自动识别蓝色区域。
    - 寻路网格根据障碍物精灵（含边界、物体、水域）构建。
    - 支持从存档数据恢复已摧毁的草丛和已击败的敌人状态。
    """

    # 水域障碍物位置缓存（地图切换时重置）
    _water_tiles_cache = None
    _water_tiles_map_id = None

    def __init__(self, level, map_id, loaded_data=None):
        """初始化地图管理器。

        参数:
            level:      Level 主类实例，加载结果写入其精灵组和属性。
            map_id:     地图标识符，用于拼接 CSV 文件路径。
            loaded_data:存档数据字典（可选），用于恢复草丛和敌人状态。
        """
        self.level = level
        self.map_id = map_id
        self.loaded_data = loaded_data

    def load(self):
        """加载并填充整个地图到 Level 的精灵组中。

        加载流程（分步骤）：
        ==================================================================
        步骤 1: 解析 4 层 CSV 布局
          - FloorBlocks（边界层）：不可通行边界，创建不可见 Tile 加入 obstacle_sprites。
          - Grass（草丛层）：可破坏装饰物，加入 visible_sprites + obstacle_sprites + attackable_sprites。
          - Objects（物体层）：静态障碍物（树/石等），加入 visible_sprites + obstacle_sprites。
          - Entities（实体层）：玩家出生点、Boss 出生点、普通敌人位置。

        步骤 2: 若无指定玩家出生点，计算地图中心为默认出生点。

        步骤 3: 处理边界层/草丛层/物体层的瓦片创建
          - 对每个非"-1"的格子，根据层类型创建对应 Tile。
          - 草丛支持存档恢复（已摧毁的草丛不再生成）。
          - 物体使用 graphics/objects 中的对应索引图片。

        步骤 4: 构建寻路网格
          - 获取地图行列数，计算像素宽高。
          - 调用 _mark_water_tiles() 标记水域为障碍物。
          - 调用 build_grid() 基于所有 obstacle_sprites 生成 0/1 网格。

        步骤 5: 处理实体层（玩家/Boss/普通敌人）
          - 玩家：新建或已有 Player 实例，支持存档数据恢复。
          - Boss：记录生成位置，调用 spawn_boss(phase=1) 生成第一阶段。
          - 普通敌人：按 ENTITY_MONSTER_MAP 映射创建 Enemy，支持存档跳过已击败敌人。
        ==================================================================
        """
        level = self.level
        map_id = self.map_id
        loaded_data = self.loaded_data

        def map_file(layer):
            """拼接指定图层的 CSV 文件路径。"""
            return f"../data/map/map_{map_id}_{layer}.csv"

        def file_or_default(path, default):
            """若专属地图文件存在则用，否则回退到默认文件。"""
            return path if os.path.exists(path) else default

        # ─── 步骤 1: 加载 4 层 CSV 布局 ───
        layouts = {
            LAYER_BOUNDARY: import_csv_layout(file_or_default(map_file('FloorBlocks'), '../data/map/map_FloorBlocks.csv')),
            LAYER_GRASS: import_csv_layout(file_or_default(map_file('Grass'), '../data/map/map_Grass.csv')),
            LAYER_OBJECT: import_csv_layout(file_or_default(map_file('Objects'), '../data/map/map_Objects.csv')),
            LAYER_ENTITIES: import_csv_layout(file_or_default(map_file('Entities'), '../data/map/map_Entities.csv')),
        }

        # ─── 步骤 2: 若未指定出生点，默认使用地图中心 ───
        if level._player_spawn_pos is None:
            map_width = len(layouts[LAYER_BOUNDARY][0]) * TILESIZE
            map_height = len(layouts[LAYER_BOUNDARY]) * TILESIZE
            level._player_spawn_pos = (map_width // 2, map_height // 2)

        # 预加载图形资源
        graphics = {
            LAYER_GRASS: import_folder('../graphics/grass'),
            LAYER_OBJECT: import_folder('../graphics/objects'),
        }

        level.pathfinding_grid = None

        # ─── 步骤 3: 边界 / 草丛 / 物体层瓦片创建 ───
        for style, layout in layouts.items():
            for row_idx, row in enumerate(layout):
                for col_idx, col in enumerate(row):
                    if col == '-1':  # 空格跳过
                        continue
                    x = col_idx * TILESIZE
                    y = row_idx * TILESIZE

                    if style == LAYER_BOUNDARY:
                        # 边界：不可见障碍物精灵，只加入 obstacle_sprites
                        Tile((x, y), [level.obstacle_sprites], SPRITE_INVISIBLE)

                    elif style == LAYER_GRASS:
                        # 草丛：检查存档中是否已被摧毁
                        destroyed = False
                        if loaded_data and 'destroyed_grass' in loaded_data:
                            for g in loaded_data['destroyed_grass']:
                                if g['x'] == x and g['y'] == y:
                                    destroyed = True
                                    break
                        if not destroyed:
                            img = choice(graphics[LAYER_GRASS])
                            Tile((x, y),
                                 [level.visible_sprites, level.obstacle_sprites, level.combat.attackable_sprites],
                                 SPRITE_GRASS, img)

                    elif style == LAYER_OBJECT:
                        # 物体（树/石等静态装饰）：可见且不可通行
                        surf = graphics[LAYER_OBJECT][int(col)]
                        Tile((x, y), [level.visible_sprites, level.obstacle_sprites],
                             SPRITE_OBJECT, surf)

        # ─── 步骤 4: 寻路网格构建 ───
        map_cols = len(layouts[LAYER_BOUNDARY][0]) if layouts[LAYER_BOUNDARY] else 0
        map_rows = len(layouts[LAYER_BOUNDARY])
        map_pixel_w = map_cols * TILESIZE
        map_pixel_h = map_rows * TILESIZE

        self._mark_water_tiles(map_cols, map_rows)
        level.pathfinding_grid = build_grid(map_pixel_w, map_pixel_h, TILESIZE, level.obstacle_sprites)

        # ─── 步骤 5: 实体层（玩家 / Boss / 普通敌人） ───
        entities_layout = layouts[LAYER_ENTITIES]
        for row_idx, row in enumerate(entities_layout):
            for col_idx, col in enumerate(row):
                if col == '-1':
                    continue
                x = col_idx * TILESIZE
                y = row_idx * TILESIZE

                if col == ENTITY_PLAYER_SPAWN:
                    # ── 玩家出生点 ──
                    if level.player is None:
                        # 首次加载：新建 Player 实例
                        spawn_pos = (x, y)
                        if level._player_spawn_pos is not None:
                            spawn_pos = level._player_spawn_pos
                        level.player = Player(
                            spawn_pos,
                            [level.visible_sprites],
                            level.obstacle_sprites,
                            level.create_attack,
                            level.destroy_attack,
                            level.create_magic)
                        if loaded_data and 'player' in loaded_data:
                            level.player.from_dict(loaded_data['player'])
                    else:
                        # 跨地图切换：复用已有 Player，更新位置和引用
                        if level._player_spawn_pos is not None:
                            level.player.pos.x, level.player.pos.y = level._player_spawn_pos
                            level.player.rect.center = level._player_spawn_pos
                            level.player.hitbox.center = level._player_spawn_pos
                        level.player.obstacle_sprites = level.obstacle_sprites
                        level.player.create_attack = level.create_attack
                        level.player.destroy_attack = level.destroy_attack
                        level.player.create_magic = level.create_magic
                        level.visible_sprites.add(level.player)
                        self._ensure_safe_spawn()  # 确保出生点不在障碍物中

                elif col == ENTITY_BOSS_SPAWN:
                    # ── Boss 出生点：记录位置，生成第一阶段 ──
                    level.boss._boss_spawn_pos = (x, y)
                    level.boss.spawn_boss(phase=1)

                else:
                    # ── 普通敌人 ──
                    defeated = False
                    if loaded_data and 'defeated_enemies' in loaded_data:
                        for e in loaded_data['defeated_enemies']:
                            if e['x'] == x and e['y'] == y:
                                defeated = True
                                break
                    if defeated:
                        continue  # 已击败的敌人不再生成
                    if col.startswith('9'):
                        continue  # 以 9 开头的为特殊预留编号，跳过
                    monster_name = ENTITY_MONSTER_MAP.get(col, 'squid')  # 默认怪物为 'squid'
                    Enemy(
                        monster_name, (x, y),
                        [level.visible_sprites, level.combat.attackable_sprites],
                        level.obstacle_sprites,
                        level.combat.damage_player,
                        level.trigger_death_particles,
                        level.add_exp,
                        lambda enemy_pos, player_pos, exp_amount=0, level=level:
                            level.trigger_exp_particles(enemy_pos, player_pos, exp_amount),
                        pathfinding_grid=level.pathfinding_grid,
                        tile_size=TILESIZE)

    # ------------------------------------------------------------------
    # Internal helpers（内部辅助方法）
    # ------------------------------------------------------------------

    def _mark_water_tiles(self, map_cols, map_rows):
        """标记水域瓦片 + 外圈边界为不可通行的障碍物（带缓存）。

        水域检测算法：
        ==================================================================
        算法分为两部分：

        1. 外圈边界封锁
           地图最外围 2 层瓦片全部强制标记为障碍物，防止玩家走出地图边界。

        2. 像素颜色检测
           加载 ground.png 底图，对每个非边界瓦片的中心像素进行采样：
           - 获取该像素的 RGBA 颜色值。
           - 判断条件：蓝色通道(c[2]) > 红色通道(c[0])
                        AND 蓝色通道(c[2]) > 绿色通道(c[1])
                        AND 蓝色通道(c[2]) > 60
           - 该条件识别"偏蓝色"的像素，即水域区域。
           - 满足条件的瓦片格子被标记为不可通行障碍物。

        缓存优化：
        - 使用类变量 _water_tiles_cache 缓存检测结果。
        - 当 map_id 改变时（地图切换），清除缓存重新检测。
        - 缓存命中时直接重放缓存的 Tile 创建，跳过像素扫描。

        参数:
            map_cols: 地图的列数（格子数）。
            map_rows: 地图的行数（格子数）。
        ==================================================================
        """
        level = self.level
        # 若地图已切换，清除缓存
        if MapManager._water_tiles_map_id != self.map_id:
            MapManager._water_tiles_cache = None
            MapManager._water_tiles_map_id = self.map_id

        # 缓存命中：直接使用缓存的障碍物列表创建 Tile
        if MapManager._water_tiles_cache is not None:
            for wx, wy in MapManager._water_tiles_cache:
                Tile((wx, wy), [level.obstacle_sprites], SPRITE_INVISIBLE)
            return

        floor_path = get_path('../graphics/tilemap/ground.png')
        MapManager._water_tiles_cache = []
        border = 2  # 外圈边界厚度（2 格）

        # ── 外圈边界封锁 ──
        for row in range(map_rows):
            for col in range(map_cols):
                if row < border or row >= map_rows - border or col < border or col >= map_cols - border:
                    MapManager._water_tiles_cache.append((col * TILESIZE, row * TILESIZE))
                    Tile((col * TILESIZE, row * TILESIZE), [level.obstacle_sprites], SPRITE_INVISIBLE)

        # ── 水域像素检测 ──
        if os.path.exists(floor_path):
            ground = pygame.image.load(floor_path).convert_alpha()
            gw, gh = ground.get_size()
            wcount = 0
            for row in range(border, map_rows - border):
                for col in range(border, map_cols - border):
                    px = col * TILESIZE + TILESIZE // 2  # 瓦片中心 x 坐标
                    py = row * TILESIZE + TILESIZE // 2  # 瓦片中心 y 坐标
                    if px < gw and py < gh:
                        c = ground.get_at((px, py))  # 采样像素颜色
                        # 蓝色通道显著高于红/绿通道 => 判定为水域
                        if c[2] > c[0] and c[2] > c[1] and c[2] > 60:
                            MapManager._water_tiles_cache.append((col * TILESIZE, row * TILESIZE))
                            Tile((col * TILESIZE, row * TILESIZE), [level.obstacle_sprites], SPRITE_INVISIBLE)
                            wcount += 1
            print(f'[MAP] {wcount} water + {len(MapManager._water_tiles_cache)-wcount} border tiles blocked ({map_cols}x{map_rows})')
        else:
            print(f'[MAP] {len(MapManager._water_tiles_cache)} border tiles blocked ({map_cols}x{map_rows})')

    def _ensure_safe_spawn(self):
        """确保玩家出生点处于可行走区域。

        如果出生点恰好位于障碍物上（跨地图切换时可能发生），
        从近到远逐层搜索最近的可行走网格，将玩家移动到该位置。

        搜索策略：
        - 使用螺旋式扩展的曼哈顿半径搜索（radius 从 1 递增）。
        - 对每个半径范围内的网格坐标，检查是否可通行（grid == 0）。
        - 找到第一个可行走位置后立即移动玩家并返回。
        """
        level = self.level
        if not level.player or not level.pathfinding_grid:
            return
        grid = level.pathfinding_grid
        gx, gy = pos_to_grid(level.player.hitbox.center, TILESIZE)
        # 若当前位置已可通行，无需调整
        if 0 <= gy < len(grid) and 0 <= gx < len(grid[0]) and grid[gy][gx] == 0:
            return
        # 螺旋搜索最近的可行走位置
        for radius in range(1, max(len(grid), len(grid[0]) if grid else 0) + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = gx + dx, gy + dy
                    if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == 0:
                        safe_pos = grid_to_pos((nx, ny), TILESIZE)
                        level.player.pos.x, level.player.pos.y = safe_pos
                        level.player.rect.center = safe_pos
                        level.player.hitbox.center = safe_pos
                        return

