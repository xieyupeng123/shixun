# -*- coding: utf-8 -*-
"""
pathfinding_utils.py — A* 寻路工具函数

提供基于 A*（A-Star）算法的网格寻路功能，以及像素坐标与网格坐标之间的转换工具。

核心函数：
    - heuristic(a, b)：估算两点间的曼哈顿距离（启发式函数）
    - astar(grid, start, goal)：在二维网格上执行 A* 寻路，返回最短路径
    - build_grid(map_width, map_height, tile_size, obstacle_sprites)：
      从 Pygame 精灵组构建寻路用的二维网格
    - pos_to_grid(pos, tile_size)：像素坐标转网格坐标
    - grid_to_pos(grid_coord, tile_size)：网格坐标转像素坐标（瓦片中心）
"""

import heapq


def heuristic(a, b):
    """
    启发式函数，估算从节点 a 到节点 b 的代价。

    使用曼哈顿距离（Manhattan Distance）作为估算值：
        h(a, b) = |a.x - b.x| + |a.y - b.y|

    曼哈顿距离适用于仅允许四方向移动（上、下、左、右）的网格，
    因为它计算的是在网格上沿垂直/水平方向移动所需的最少步数。

    参数:
        a (tuple): 起点网格坐标 (x, y)
        b (tuple): 终点网格坐标 (x, y)

    返回:
        int: 曼哈顿距离值
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    """
    A*（A-Star）寻路算法。

    在给定的二维网格上，寻找从 start 到 goal 的最短路径。
    算法综合了 Dijkstra（已消耗代价 g）和贪心最佳优先搜索（预估代价 h），
    通过 f = g + h 选择最优节点进行扩展。

    参数:
        grid (list[list[int]]): 二维网格，0 表示可行走，1 表示障碍物
        start (tuple): 起点网格坐标 (x, y)
        goal (tuple): 终点网格坐标 (x, y)

    返回:
        list[tuple]: 从 start 到 goal 的路径坐标列表（含两端），
                     如果无法到达则返回空列表 []

    算法步骤：
        1. 边界检查：确保 start 和 goal 在网格范围内且都不是障碍物
        2. 初始化：
           - close_set：已探索的节点集合
           - came_from：记录每个节点来自哪个父节点（用于路径回溯）
           - gscore：从起点到每个节点的实际代价
           - fscore：gscore + heuristic，即节点优先级
           - oheap：优先队列（最小堆），按 fscore 排序
        3. 主循环：从优先队列中取出 f 值最小的节点
           - 若当前节点 == goal，则回溯 came_from 构建路径并返回
           - 否则将当前节点加入 close_set，扩展四个方向的邻居
        4. 邻居处理：
           - 检查邻居是否在网格范围内且可行走
           - 若已在 close_set 且新代价不低于已知代价，跳过
           - 若有更优路径，更新 came_from、gscore、fscore 并入队
        5. 如果优先队列为空仍未到达 goal，返回空列表
    """
    # 四方向移动向量：右、左、上、下
    neighbors = [(0, 1), (1, 0), (-1, 0), (0, -1)]

    # ── 步骤 1：边界检查 ──────────────────────────────────────────────
    # 检查 start 和 goal 是否在网格范围内
    if not (0 <= start[0] < len(grid[0]) and 0 <= start[1] < len(grid)) \
       or not (0 <= goal[0] < len(grid[0]) and 0 <= goal[1] < len(grid)):
        return []
    # 检查起点或终点是否为障碍物
    if grid[start[1]][start[0]] == 1 or grid[goal[1]][goal[0]] == 1:
        return []

    # ── 步骤 2：初始化数据结构 ─────────────────────────────────────────
    close_set = set()                    # 已探索的节点集合（不再需要处理）
    came_from = {}                       # 父节点映射表：{子节点: 父节点}，用于路径回溯
    gscore = {start: 0}                  # g(n)：从起点到节点 n 的实际代价
    fscore = {start: heuristic(start, goal)}  # f(n) = g(n) + h(n)，优先级
    oheap = []                           # 优先队列（最小堆），按 fscore 排序
    heapq.heappush(oheap, (fscore[start], start))  # 将起点入队

    # ── 步骤 3：A* 主循环 ─────────────────────────────────────────────
    while oheap:
        # 弹出 f 值最小的节点（当前最优节点）
        current = heapq.heappop(oheap)[1]

        # ── 到达目标？回溯路径 ─────────────────────────────────────────
        if current == goal:
            # 回溯：从 goal 开始沿 came_from 反向遍历到 start
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()  # 反转得到从 start 到 goal 的顺序
            return path

        # 将当前节点标记为已探索
        close_set.add(current)

        # ── 步骤 4：扩展四个方向的邻居节点 ─────────────────────────────
        for i, j in neighbors:
            neighbor = (current[0] + i, current[1] + j)  # 计算邻居坐标
            tentative_g_score = gscore[current] + 1        # 从起点经过 current 到 neighbor 的代价

            # ── 检查邻居是否在网格范围内且可行走 ─────────────────────
            if 0 <= neighbor[0] < len(grid[0]) and 0 <= neighbor[1] < len(grid):
                if grid[neighbor[1]][neighbor[0]] == 1:  # 障碍物，跳过
                    continue
            else:
                continue  # 超出网格边界，跳过

            # ── 剪枝：已在 close_set 且当前路径没有更优 ──────────────
            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, float('inf')):
                continue

            # ── 发现更优路径？更新代价并入队 ─────────────────────────
            if tentative_g_score < gscore.get(neighbor, float('inf')):
                came_from[neighbor] = current                                        # 记录父节点
                gscore[neighbor] = tentative_g_score                                 # 更新 g(n)
                fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)     # 更新 f(n) = g(n) + h(n)
                heapq.heappush(oheap, (fscore[neighbor], neighbor))                  # 将邻居入队

    # ── 步骤 5：优先队列耗尽仍未找到目标，无可行路径 ─────────────────
    return []


def build_grid(map_width, map_height, tile_size, obstacle_sprites):
    """
    根据地图尺寸和障碍物精灵组构建寻路用的二维网格。

    将地图划分为 tile_size × tile_size 的格子，
    每个格子标记为 0（可行走）或 1（障碍物）。

    参数:
        map_width (int): 地图总宽度（像素）
        map_height (int): 地图总高度（像素）
        tile_size (int): 单个瓦片的像素尺寸（与寻路网格的分辨率一致）
        obstacle_sprites (pygame.sprite.Group): 所有障碍物精灵的组，
            每个精灵的 rect 位置将被映射到网格上标记为障碍物

    返回:
        list[list[int]]: 二维网格，grid[y][x] = 0 表示可行走，1 表示障碍物
    """
    grid_w = map_width // tile_size     # 网格列数
    grid_h = map_height // tile_size    # 网格行数
    # 初始化全 0 网格（所有格子默认可行走）
    grid = [[0 for _ in range(grid_w)] for _ in range(grid_h)]
    # 遍历所有障碍物精灵，将对应网格位置标记为 1
    for sprite in obstacle_sprites:
        x = int(sprite.rect.x // tile_size)   # 精灵左上角 x 对应的网格列
        y = int(sprite.rect.y // tile_size)   # 精灵左上角 y 对应的网格行
        if 0 <= x < grid_w and 0 <= y < grid_h:
            grid[y][x] = 1  # 标记为障碍物
    return grid


def pos_to_grid(pos, tile_size):
    """
    将像素坐标转换为网格坐标。

    注意：这里将像素坐标向下取整对齐到网格，
    因此同一个格子内的所有像素坐标映射到同一个网格坐标。

    参数:
        pos (tuple): 像素坐标 (x, y)
        tile_size (int): 单个瓦片的像素尺寸

    返回:
        tuple: 网格坐标 (grid_x, grid_y)
    """
    return (int(pos[0] // tile_size), int(pos[1] // tile_size))


def grid_to_pos(grid_coord, tile_size):
    """
    将网格坐标转换为像素坐标（返回瓦片中心点的像素位置）。

    参数:
        grid_coord (tuple): 网格坐标 (grid_x, grid_y)
        tile_size (int): 单个瓦片的像素尺寸

    返回:
        tuple: 瓦片中心的像素坐标 (pixel_x, pixel_y)
    """
    return (grid_coord[0] * tile_size + tile_size // 2,
            grid_coord[1] * tile_size + tile_size // 2)
