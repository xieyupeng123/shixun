"""A* pathfinding for enemy AI."""
import heapq


def astar(grid, start, goal):
    """Return list of (x, y) from start to goal, or [] if no path."""
    if not (0 <= start[0] < len(grid[0]) and 0 <= start[1] < len(grid)):
        return []
    if not (0 <= goal[0] < len(grid[0]) and 0 <= goal[1] < len(grid)):
        return []
    if grid[start[1]][start[0]] == 1 or grid[goal[1]][goal[0]] == 1:
        return []

    neighbors = [(0, 1), (1, 0), (-1, 0), (0, -1)]
    close_set = set()
    came_from = {}
    gscore = {start: 0}
    fscore = {start: _heuristic(start, goal)}
    oheap = [(fscore[start], start)]

    while oheap:
        current = heapq.heappop(oheap)[1]
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        close_set.add(current)
        for dx, dy in neighbors:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < len(grid[0]) and 0 <= neighbor[1] < len(grid):
                if grid[neighbor[1]][neighbor[0]] == 1:
                    continue
            else:
                continue
            tentative_g = gscore[current] + 1
            if neighbor in close_set and tentative_g >= gscore.get(neighbor, float('inf')):
                continue
            if tentative_g < gscore.get(neighbor, float('inf')):
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g
                fscore[neighbor] = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(oheap, (fscore[neighbor], neighbor))
    return []


def _heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def build_grid(map_width, map_height, tile_size, obstacle_sprites):
    """Build 2D grid: 0=walkable, 1=obstacle."""
    grid_w = map_width // tile_size
    grid_h = map_height // tile_size
    grid = [[0 for _ in range(grid_w)] for _ in range(grid_h)]
    for sprite in obstacle_sprites:
        x = int(sprite.rect.x // tile_size)
        y = int(sprite.rect.y // tile_size)
        if 0 <= x < grid_w and 0 <= y < grid_h:
            grid[y][x] = 1
    return grid


def pos_to_grid(pos, tile_size):
    return (int(pos[0] // tile_size), int(pos[1] // tile_size))


def grid_to_pos(grid_coord, tile_size):
    return (grid_coord[0] * tile_size + tile_size // 2,
            grid_coord[1] * tile_size + tile_size // 2)
