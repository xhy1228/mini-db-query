#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小程序图标生成脚本

用于生成统一风格的科技感图标
"""

from PIL import Image, ImageDraw
import os
import math

# 图标保存目录
ICON_DIR = os.path.join(os.path.dirname(__file__), '../miniapp/images')


def create_tech_icon(name, draw_func, is_active=False):
    """创建科技感图标"""
    size = 162  # 2x 高清
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 颜色
    if is_active:
        primary = (24, 144, 255)
        secondary = (64, 169, 255)
    else:
        primary = (153, 153, 153)
        secondary = (180, 180, 180)
    
    # 绘制背景圆形发光
    cx, cy = size // 2, size // 2
    radius = 60
    for r in range(radius, 0, -2):
        alpha = int(255 * (1 - r/radius) * 0.3)
        if is_active:
            color = (24, 144, 255, alpha)
        else:
            color = (153, 153, 153, alpha)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    
    # 调用绘制函数
    draw_func(draw, cx, cy, 50, primary, secondary)
    
    # 保存为81x81 (标准尺寸)
    img_small = img.resize((81, 81), Image.Resampling.LANCZOS)
    os.makedirs(ICON_DIR, exist_ok=True)
    img_small.save(os.path.join(ICON_DIR, f'{name}.png'), 'PNG')
    print(f'Created {name}.png')


def draw_home(draw, cx, cy, size, primary, secondary):
    """绘制房子图标"""
    roof_points = [
        (cx, cy - size//2 - 5),
        (cx - size//2, cy),
        (cx + size//2, cy),
    ]
    draw.polygon(roof_points, fill=primary)
    house_rect = [cx - size//3, cy, cx + size//3, cy + size//2]
    draw.rectangle(house_rect, fill=primary)
    door_rect = [cx - size//8, cy + size//4, cx + size//8, cy + size//2]
    draw.rectangle(door_rect, fill=(255, 255, 255, 200))


def draw_search(draw, cx, cy, size, primary, secondary):
    """绘制搜索图标"""
    r = size // 2 - 5
    draw.ellipse([cx-r, cy-r-5, cx+r, cy+r-5], outline=primary, width=6)
    handle_start = (cx + int(r*0.7), cy + int(r*0.7) - 5)
    handle_end = (cx + size//2, cy + size//2)
    draw.line([handle_start, handle_end], fill=primary, width=6)


def draw_history(draw, cx, cy, size, primary, secondary):
    """绘制历史/时钟图标"""
    r = size // 2 - 5
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=primary, width=5)
    draw.line([(cx, cy), (cx, cy - r//2)], fill=primary, width=5)
    draw.line([(cx, cy), (cx + r//2, cy)], fill=primary, width=5)


def draw_profile(draw, cx, cy, size, primary, secondary):
    """绘制用户图标"""
    head_r = size // 4
    draw.ellipse([cx-head_r, cy-size//3, cx+head_r, cy+head_r-size//3], fill=primary)
    body_points = [
        (cx - size//2, cy + size//2),
        (cx - size//3, cy),
        (cx + size//3, cy),
        (cx + size//2, cy + size//2),
    ]
    draw.polygon(body_points, fill=primary)


def create_default_avatar():
    """创建默认用户头像"""
    size = 200
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    
    for r in range(100, 0, -1):
        ratio = r / 100
        color = (
            int(24 + (64 - 24) * (1 - ratio)),
            int(144 + (169 - 144) * (1 - ratio)),
            255,
            255
        )
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    
    head_r = 30
    draw.ellipse([cx-head_r, cy-35, cx+head_r, cy+head_r-35], fill=(255, 255, 255, 230))
    
    body_points = [
        (cx - 50, cy + 70),
        (cx - 35, cy + 10),
        (cx + 35, cy + 10),
        (cx + 50, cy + 70),
    ]
    draw.polygon(body_points, fill=(255, 255, 255, 230))
    
    os.makedirs(ICON_DIR, exist_ok=True)
    img.save(os.path.join(ICON_DIR, 'default-avatar.png'), 'PNG')
    print('Created default-avatar.png')


def create_logo():
    """创建应用Logo"""
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    
    for r in range(250, 200, -1):
        alpha = int(255 * (250 - r) / 50 * 0.3)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(24, 144, 255, alpha))
    
    for r in range(200, 0, -1):
        ratio = r / 200
        if ratio > 0.9:
            color = (64, 169, 255, 255)
        else:
            color = (24, 144, 255, 255)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    
    r = 80
    draw.ellipse([cx-r, cy-r-20, cx+r, cy+r-20], outline=(255, 255, 255, 255), width=15)
    handle_start = (cx + int(r*0.7), cy + int(r*0.7) - 20)
    handle_end = (cx + 120, cy + 80)
    draw.line([handle_start, handle_end], fill=(255, 255, 255, 255), width=15)
    
    os.makedirs(ICON_DIR, exist_ok=True)
    img.save(os.path.join(ICON_DIR, 'logo.png'), 'PNG')
    print('Created logo.png')


def create_empty_icon():
    """创建空状态图标"""
    size = 160
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    draw.rounded_rectangle([20, 10, 140, 150], radius=10, outline=(153, 153, 153, 150), width=4)
    draw.polygon([(100, 10), (140, 10), (140, 50)], fill=(153, 153, 153, 100))
    for y in [60, 80, 100]:
        draw.line([(40, y), (120, y)], fill=(153, 153, 153, 100), width=3)
    
    os.makedirs(ICON_DIR, exist_ok=True)
    img.save(os.path.join(ICON_DIR, 'empty.png'), 'PNG')
    print('Created empty.png')


def main():
    """生成所有图标"""
    print('Generating icons...\n')
    
    # TabBar 图标
    icons_config = [
        ('home', draw_home, False),
        ('home-active', draw_home, True),
        ('query', draw_search, False),
        ('query-active', draw_search, True),
        ('history', draw_history, False),
        ('history-active', draw_history, True),
        ('profile', draw_profile, False),
        ('profile-active', draw_profile, True),
    ]
    
    for name, draw_func, is_active in icons_config:
        create_tech_icon(name, draw_func, is_active)
    
    # 其他图标
    create_default_avatar()
    create_logo()
    create_empty_icon()
    
    print('\nAll icons generated successfully!')


if __name__ == '__main__':
    main()
