# Stardew Valley Action X — Final Version (V10)

俯视角像素风动作角色扮演游戏 — 以《星露谷物语》矿洞战斗为灵感

## 🎮 游戏特色

- **5种武器**：剑/矛/斧/细剑/叉，各有独立伤害和冷却
- **2种魔法**：火焰术（前方AOE）+ 治疗术（回血）
- **4种怪物**：鱿鱼/浣熊/精灵/竹子，AI状态机 + A*寻路
- **Boss三阶段**：属性×1→×2→×4，颜色变化，击杀3次胜利
- **无敌模式**：速度×2，攻击×2，金色光效，免疫伤害
- **升级系统**：五维属性分配（生命/能量/攻击/魔法/速度）
- **存档系统**：JSON原子写入，启动时继续/新游戏
- **世界地图**：全屏覆盖，敌人/Boss/玩家位置实时显示
- **完整音效**：背景音乐 + 区域BGM切换 + 攻击/受伤/死亡音效
- **12种粒子特效**：火焰/光环/治疗/爪击/斩击/雷电/草叶等

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Pygame 2.x

### 安装运行
```bash
pip install pygame
cd stardew-valley-action-x-final/code
python main.py
```

## 🎯 操作说明

| 按键 | 功能 |
|------|------|
| WASD / 方向键 | 移动 |
| 鼠标左键 | 攻击 |
| 鼠标右键 | 释放魔法 |
| Q键 / 鼠标滚轮 | 切换武器 |
| E键 | 切换魔法 |
| 空格 | 切换无敌模式 |
| B键 | 升级菜单（暂停） |
| M键 | 世界地图 |
| P键 | 暂停时存档 |
| 回车 | 开始游戏 |
| R键 | 重开 |
| ESC | 退出 |

## 📁 项目结构

```
stardew-valley-action-x-final/
├── code/                    # 20个Python源文件（2828行）
│   ├── main.py              # 游戏入口（421行）
│   ├── level.py             # 关卡协调者（460行）
│   ├── player.py            # 玩家类（361行）
│   ├── enemy.py             # 敌人类（256行）
│   ├── map_manager.py       # 地图加载（233行）
│   ├── ui.py                # HUD界面（185行）
│   ├── particles.py         # 粒子特效（167行）
│   ├── upgrade.py           # 升级菜单（158行）
│   ├── entity.py            # Entity基类（83行）
│   ├── pathfinding_utils.py # A*寻路（78行）
│   ├── resource_manager.py  # 资源缓存（61行）
│   ├── magic.py             # 魔法系统（59行）
│   ├── support.py           # 工具函数（41行）
│   ├── sound_manager.py     # 音效管理（37行）
│   ├── save_manager.py      # 存档系统（36行）
│   ├── settings.py          # 配置数据（91行）
│   ├── constants.py         # 常量定义（30行）
│   ├── weapon.py            # 武器精灵（28行）
│   ├── music_state.py       # BGM状态（26行）
│   └── tile.py              # 瓦片精灵（17行）
├── data/map/                # CSV地图数据
├── graphics/                # PNG图片资源
├── audio/                   # 音频资源
├── font/                    # 字体文件
├── CHANGELOG.md             # 更新日志
└── README.md                # 本文件
```

## 🏗️ 架构设计

### 四层分层架构
- **控制层**：Game(main.py), UI, Upgrade
- **逻辑层**：Level, CombatManager, BossManager, MapManager
- **实体层**：Player, Enemy, Weapon, MagicPlayer, Tile
- **数据层**：settings.py, ResourceManager, Pathfinding, SaveManager

### 核心设计原则
- 上层依赖下层，下层不依赖上层
- 同层通过回调函数通信
- Level通过组合模式集成三个Manager
- ResourceManager单例模式
- 数据驱动设计（配置集中在settings.py）
- Delta Time驱动（帧率无关）
- 分轴AABB碰撞检测
- Y轴深度排序渲染

## 📊 版本历史

| 版本 | 代码量 | 文件数 | 关键特性 |
|------|--------|--------|----------|
| V1 | 343行 | 7 | 窗口+移动+地图 |
| V2 | 475行 | 7 | 主菜单+攻击 |
| V3 | 890行 | 14 | 敌人AI+HP+HUD |
| V4 | 1192行 | 18 | 5种武器+A*寻路 |
| V5 | 1268行 | 18 | 真实精灵+粒子+存档 |
| V8 | 1665行 | 20 | Boss+魔法+升级+暂停 |
| V9 | 1997行 | 20 | 架构重构+三阶段Boss+世界地图 |
| **V10** | **2828行** | **20** | **无敌+音效+BGM+UI** |

详见 [CHANGELOG.md](CHANGELOG.md)

## 📝 开发文档

- 需求规格说明书（SRS）
- 概要设计说明书（HLD）
- 设计与实现文档

## 📄 许可证

MIT License
