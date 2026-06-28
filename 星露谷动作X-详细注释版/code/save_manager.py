# -*- coding: utf-8 -*-
"""
save_manager.py — 存档管理器

提供游戏存档的保存与加载功能。

核心特性：
    - 使用 JSON 格式存储游戏状态（玩家属性、背包物品、地图状态等）
    - 原子写入机制：先写入临时文件再重命名，避免写入中断导致存档损坏
    - 保存失败时自动清理临时文件
    - 加载失败时返回 None 而不是抛出异常
"""

import json
import os
import tempfile


def save_game(data, filepath='savegame.json'):
    """
    将游戏状态原子性地保存到 JSON 文件。

    原子写入策略（防止存档损坏）：
        1. 在目标文件所在目录下创建一个临时文件（mkstemp）
        2. 将数据写入临时文件
        3. 写入成功后，使用 os.replace() 将临时文件原子性地重命名为目标文件
        4. 如果在写入过程中程序崩溃或被中断，临时文件会被保留但目标文件不受影响
        5. 如果写入过程中发生异常，显式清理临时文件

    参数:
        data (dict): 要保存的游戏状态数据，将被序列化为 JSON
        filepath (str): 目标存档文件的路径，默认 'savegame.json'

    异常处理:
        - 任何异常都会被捕获并打印错误信息，不会让调用方崩溃
    """
    try:
        # 获取目标文件所在目录（如果 filepath 不包含目录，使用当前目录 '.'）
        dir_name = os.path.dirname(filepath) or '.'

        # 在目标目录下创建一个临时文件，后缀为 '.tmp'
        # mkstemp 返回 (文件描述符, 临时文件路径)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')

        try:
            # 通过文件描述符打开临时文件进行写入
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=4)  # 序列化数据并写入临时文件

            # 原子重命名：将临时文件替换为目标文件
            # os.replace() 是原子操作（在 POSIX 系统上为 rename()，
            # Windows 上为 MoveFileEx()），保证写入完整性：
            #   - 如果程序在这之前崩溃 → 临时文件残留，原文件完好
            #   - 如果程序在这之后崩溃 → 目标文件已完整写入
            os.replace(tmp_path, filepath)

        except Exception:
            # 写入过程中出错 → 清理临时文件，避免残留垃圾文件
            try:
                os.unlink(tmp_path)  # 删除临时文件
            except OSError:
                pass  # 如果删除失败也忽略（文件可能不存在）
            raise  # 重新抛出原始异常

    except Exception as e:
        # 捕获并打印所有保存相关的错误，不向上传播
        print(f'[ERROR] Failed to save game: {e}')


def load_game(filepath='savegame.json'):
    """
    从 JSON 文件中加载游戏状态。

    参数:
        filepath (str): 存档文件的路径，默认 'savegame.json'

    返回:
        dict | None: 如果文件存在且解析成功，返回游戏状态字典；
                     如果文件不存在或解析失败，返回 None

    异常处理:
        - 文件不存在 → 静默返回 None（首次启动时的正常情况）
        - JSON 格式错误 → 返回 None（存档损坏或版本不兼容）
    """
    if not os.path.exists(filepath):
        return None  # 存档文件不存在，可能是首次运行
    try:
        with open(filepath, 'r') as f:
            return json.load(f)  # 解析 JSON 并返回字典
    except Exception:
        # 文件存在但读取或解析失败（如格式损坏），返回 None
        return None
