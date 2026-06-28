"""
游戏常量定义模块 (Game Constants)

本模块集中管理所有游戏中使用到的枚举值与字符串常量，包括：
- 实体CSV编码：在地图CSV文件中用于标识不同实体（玩家出生点、怪物等）
- 精灵类型：区分不同交互对象的类别
- 地图图层名称：Tiled地图中各图层的字符串标识

将这些散落在代码中的字面量集中在此处，可以避免硬编码字符串散落各处，
提高代码的可维护性和可读性。
"""


# ── 实体CSV编码 (Entity CSV Codes) ──────────────────────────────────────────
# 这些编码用于地图CSV文件（map_Entities.csv）中，
# 程序通过读取CSV中的这些数值来确定在何处生成何种实体

ENTITY_PLAYER_SPAWN = '394'   # 玩家出生点的CSV编码
ENTITY_BOSS_SPAWN = '392'     # Boss生成点的CSV编码
ENTITY_BAMBOO = '390'         # 竹子怪（bamboo）的CSV编码
ENTITY_SPIRIT = '391'         # 幽灵（spirit）的CSV编码
ENTITY_SQUID = '393'          # 鱿鱼怪（squid）的CSV编码

# 实体CSV编码到怪物名称的映射字典
# 用于将CSV文件中读出的数字编码转换为游戏逻辑中使用的字符串名称
# 注意：浣熊怪（raccoon）在此映射中不存在，可能通过其他方式生成
ENTITY_MONSTER_MAP = {
    ENTITY_BAMBOO: 'bamboo',   # 编码 '390' -> 竹子怪
    ENTITY_SPIRIT: 'spirit',   # 编码 '391' -> 幽灵
    ENTITY_SQUID: 'squid',     # 编码 '393' -> 鱿鱼怪
}

# ── 精灵类型常量 (Sprite Types) ─────────────────────────────────────────────
# 用于在碰撞检测和交互逻辑中区分不同类别的精灵

SPRITE_GRASS = 'grass'        # 草丛：可被玩家破坏，掉落物品
SPRITE_OBJECT = 'object'      # 物体（箱子/装饰物等）：可交互，可能有碰撞体积
SPRITE_INVISIBLE = 'invisible' # 不可见碰撞体：仅用于阻挡玩家移动，无视觉表现

# ── 地图图层名称 (Map Layer Names) ──────────────────────────────────────────
# 对应Tiled地图编辑器中的图层命名，用于程序按名称读取不同图层

LAYER_BOUNDARY = 'boundary'   # 边界层：定义地图边界和障碍物区域
LAYER_GRASS = 'grass'         # 草丛层：定义可破坏草丛的位置
LAYER_OBJECT = 'object'       # 物体层：定义可交互物体（箱子等）的位置
LAYER_ENTITIES = 'entities'   # 实体层：定义玩家出生点和怪物生成位置
