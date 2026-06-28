"""
工具函数模块 (Support / Utility Functions)

本模块提供游戏各模块通用的辅助函数，包括：
- get_path()      : 将相对路径转换为相对于本文件的绝对路径，确保资源加载不受工作目录影响
- import_csv_layout() : 读取Tiled导出的CSV格式地图布局文件，返回二维列表
- import_folder() : 批量加载文件夹中的所有图片资源，返回pygame.Surface对象列表

这些函数抽象了文件IO和资源加载的通用逻辑，被 settings.py 和各个游戏场景广泛调用。
"""

import os       # 标准库：用于路径操作和目录遍历
import pygame   # 游戏引擎库：用于加载和处理图像资源
from csv import reader  # CSV解析器：用于读取逗号分隔的布局文件


def get_path(path: str) -> str:
    """
    将相对路径转换为相对于本文件（support.py）所在目录的绝对路径。

    该函数确保无论程序从哪个工作目录启动，资源路径都能正确解析。
    这是整个游戏资源加载的基础工具函数。

    Args:
        path (str): 相对于 code/ 目录的相对路径。
                    例如：'../graphics/weapons/sword/full.png'
                          '../audio/flame.wav'
                          '../font/joystix.ttf'

    Returns:
        str: 拼接后的绝对路径。
             例如：'C:/Users/.../星露谷动作X-详细注释版/graphics/weapons/sword/full.png'
    """
    # 获取当前文件（support.py）所在的目录绝对路径
    absolute_path = os.path.dirname(__file__)
    # 将相对路径拼接到当前目录上
    full_path = os.path.join(absolute_path, path)

    return full_path


def import_csv_layout(path: str) -> list:
    """
    读取Tiled地图编辑器导出的CSV格式地图布局文件。

    地图布局CSV是一个二维网格，每个单元格的值代表对应位置的地图元素编码。
    例如：'0' 表示空地，'394' 表示玩家出生点等。
    这些编码在 constants.py 中有对应的命名常量。

    Args:
        path (str): CSV文件的相对路径（相对于 code/ 目录）。
                    例如：'../map/map_Block.csv'

    Returns:
        list: 二维列表，每个元素是一个字符串列表。
              例如：[['0', '0', '394', ...], ['0', '390', '0', ...], ...]
              如果文件不存在或读取失败，返回空列表 []。

    Raises:
        FileNotFoundError: 文件不存在时被捕获并打印错误信息，不抛出。
        Exception: 其他IO错误被捕获并打印错误信息，不抛出。
    """
    # 将相对路径转换为绝对路径
    unique_path = get_path(path)
    # 用于存储解析后的地图数据
    terrain_map = []
    try:
        # 以只读方式打开CSV文件
        with open(unique_path) as level_map:
            # 创建CSV读取器，指定逗号为分隔符
            layout = reader(level_map, delimiter=',')
            # 逐行读取，将每行的字符串列表添加到地图数据中
            for row in layout:
                terrain_map.append(list(row))
    except FileNotFoundError:
        # CSV文件不存在时打印错误并返回空列表
        print(f'[ERROR] CSV file not found: {unique_path}')
        return []
    except Exception as e:
        # 其他未知错误也打印错误并返回空列表
        print(f'[ERROR] Failed to read CSV {unique_path}: {e}')
        return []
    return terrain_map


def import_folder(path: str) -> list:
    """
    批量加载指定文件夹中的所有图片文件，返回pygame Surface对象列表。

    这个函数常用于加载精灵动画的序列帧图片。
    它会自动对文件名进行排序，确保帧的顺序正确。

    Args:
        path (str): 图片文件夹的相对路径（相对于 code/ 目录）。
                    例如：'../graphics/player/' 或 '../graphics/particles/flame/'

    Returns:
        list[pygame.Surface]: pygame Surface对象列表，每个元素对应一张加载好的图片。
                              图片已通过 convert_alpha() 转换，支持透明通道。
                              如果文件夹为空，返回空列表 []。

    注意：
        - 使用 os.walk() 遍历文件夹，仅获取文件（忽略子目录）
        - 文件按字母顺序排序 (img_files.sort())，因此建议文件名用数字前缀
          控制帧顺序，如 'frame_001.png', 'frame_002.png', ...
        - 每张图片都调用 convert_alpha() 以优化渲染性能并保留透明通道
    """
    # 将相对路径转换为绝对路径
    unique_path = get_path(path)
    # 用于存储加载后的Surface对象
    surface_list = []

    # 遍历目标文件夹
    # os.walk 返回 (当前路径, 子目录列表, 文件名列表) 三元组
    # 使用下划线忽略当前路径和子目录列表，只取文件名列表
    for _, __, img_files in os.walk(unique_path):
        # 对文件名排序，保证帧的播放顺序正确
        img_files.sort()
        # 逐个加载图片文件
        for image in img_files:
            # 构造完整的文件路径
            full_path = os.path.join(unique_path, image)
            # 使用pygame加载图片，并转换为带透明通道的格式
            image_surf = pygame.image.load(full_path).convert_alpha()
            # 将加载好的Surface添加到列表中
            surface_list.append(image_surf)

    return surface_list
