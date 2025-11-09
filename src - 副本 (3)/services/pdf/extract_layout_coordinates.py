# -*- coding: utf-8 -*-
"""
提取标准PDF的详细布局坐标
专注于关键元素：标题框、复选框、方格、分隔线等
"""

import pdfplumber
import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_layout(pdf_path):
    """提取PDF布局关键坐标"""
    layout = {
        'page_size': {},
        'borders': [],
        'gray_boxes': [],  # 灰色背景框
        'title_area': {},  # 标题区
        'checkboxes': [],  # 复选框
        'id_boxes': [],    # ID号码框
        'separators': [],  # 分隔线
        'text_positions': {}
    }

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]

        # 页面尺寸
        layout['page_size'] = {
            'width': page.width,
            'height': page.height
        }

        # 识别灰色背景矩形（通过填充色）
        for rect in page.rects:
            # 判断是否为小矩形（可能是框或背景）
            width = rect['x1'] - rect['x0']
            height = rect['y1'] - rect['y0']
            area = width * height

            # 大矩形（边框）
            if area > 200000:
                layout['borders'].append({
                    'x': rect['x0'],
                    'y': rect['y0'],
                    'width': width,
                    'height': height,
                    'linewidth': rect.get('linewidth', 0)
                })
            # 中等矩形（可能是标题框或灰色背景）
            elif 5000 < area < 200000:
                layout['gray_boxes'].append({
                    'x': rect['x0'],
                    'y': rect['y0'],
                    'width': width,
                    'height': height,
                    'linewidth': rect.get('linewidth', 0),
                    'area': area
                })
            # 小矩形（复选框或ID框）
            elif area < 500:
                if 50 < area < 200:  # 复选框大小
                    layout['checkboxes'].append({
                        'x': rect['x0'],
                        'y': rect['y0'],
                        'size': width
                    })
                elif 200 <= area < 500:  # ID框大小
                    layout['id_boxes'].append({
                        'x': rect['x0'],
                        'y': rect['y0'],
                        'width': width,
                        'height': height
                    })

        # 识别水平分隔线
        for line in page.lines:
            # 水平线
            if abs(line['y0'] - line['y1']) < 1:
                length = abs(line['x1'] - line['x0'])
                if length > 200:  # 长线可能是分隔线
                    layout['separators'].append({
                        'type': 'horizontal',
                        'x': line['x0'],
                        'y': line['y0'],
                        'length': length,
                        'linewidth': line.get('linewidth', 0)
                    })

        # 提取关键文本位置
        chars = page.chars
        if chars:
            # 查找标题文本
            title_chars = [c for c in chars if 'แบบรายงาน' in c.get('text', '')]
            if title_chars:
                layout['text_positions']['title'] = {
                    'x': title_chars[0]['x0'],
                    'y': title_chars[0]['y0'],
                    'size': title_chars[0].get('size', 0)
                }

            # 查找区域标题
            for section in ['ส่วนที่ ๑', 'ส่วนที่ ๒', 'ส่วนที่ ๓', 'ส่วนที่ ๔']:
                section_chars = [c for c in chars if section in c.get('text', '')]
                if section_chars:
                    layout['text_positions'][section] = {
                        'x': section_chars[0]['x0'],
                        'y': section_chars[0]['y0']
                    }

    return layout

def analyze_zones(layout):
    """分析各个区域"""
    zones = {}

    # 边框按大小排序
    borders = sorted(layout['borders'], key=lambda b: b['width'] * b['height'], reverse=True)
    if len(borders) >= 3:
        zones['border_outer'] = borders[0]
        zones['border_middle'] = borders[1]
        zones['border_inner'] = borders[2]

    # 灰色框按y坐标排序（从上到下）
    gray_boxes = sorted(layout['gray_boxes'], key=lambda b: -b['y'])
    if gray_boxes:
        zones['title_box'] = gray_boxes[0]  # 最上面的灰色框应该是标题框
        if len(gray_boxes) > 1:
            zones['section_boxes'] = gray_boxes[1:5]  # 区域标题框

    # 分隔线按y坐标排序
    separators = sorted(layout['separators'], key=lambda s: -s['y'])
    zones['separators'] = separators[:10]  # 前10条分隔线

    # 复选框按y坐标分组
    checkboxes = sorted(layout['checkboxes'], key=lambda cb: -cb['y'])
    zones['checkbox_positions'] = checkboxes[:20]  # 前20个复选框

    # ID框
    id_boxes = sorted(layout['id_boxes'], key=lambda ib: ib['x'])
    zones['id_box_positions'] = id_boxes[:13]  # 13位ID框

    return zones

if __name__ == '__main__':
    pdf_path = r'D:\Code\ExchangeNew\src\test_output\OK\รายงาน ปปง 1-01 ซื้อขายเกิน 500,000 บาท ยกเว้นเงินบาทแลก.pdf'

    print(f"提取布局坐标: {pdf_path}\n")

    layout = extract_layout(pdf_path)
    zones = analyze_zones(layout)

    # 输出关键信息
    print("=" * 60)
    print("三层边框:")
    print("=" * 60)
    for key in ['border_outer', 'border_middle', 'border_inner']:
        if key in zones:
            b = zones[key]
            print(f"{key}:")
            print(f"  位置: ({b['x']:.2f}, {b['y']:.2f})")
            print(f"  尺寸: {b['width']:.2f} x {b['height']:.2f}")
            print(f"  线宽: {b['linewidth']:.2f}")
            print()

    print("=" * 60)
    print("标题框和区域框:")
    print("=" * 60)
    if 'title_box' in zones:
        tb = zones['title_box']
        print(f"标题框:")
        print(f"  位置: ({tb['x']:.2f}, {tb['y']:.2f})")
        print(f"  尺寸: {tb['width']:.2f} x {tb['height']:.2f}")
        print()

    if 'section_boxes' in zones:
        print("区域标题框 (前3个):")
        for i, sb in enumerate(zones['section_boxes'][:3]):
            print(f"  框{i+1}: 位置({sb['x']:.2f}, {sb['y']:.2f}), 尺寸{sb['width']:.2f}x{sb['height']:.2f}")

    print("\n" + "=" * 60)
    print("分隔线 (前5条):")
    print("=" * 60)
    for i, sep in enumerate(zones.get('separators', [])[:5]):
        print(f"分隔线{i+1}: y={sep['y']:.2f}, 长度={sep['length']:.2f}, 线宽={sep.get('linewidth', 0):.2f}")

    print("\n" + "=" * 60)
    print("复选框位置 (前10个):")
    print("=" * 60)
    for i, cb in enumerate(zones.get('checkbox_positions', [])[:10]):
        print(f"复选框{i+1}: ({cb['x']:.2f}, {cb['y']:.2f}), 尺寸={cb['size']:.2f}")

    print("\n" + "=" * 60)
    print("ID框位置 (前13个):")
    print("=" * 60)
    for i, ib in enumerate(zones.get('id_box_positions', [])[:13]):
        print(f"ID框{i+1}: ({ib['x']:.2f}, {ib['y']:.2f}), {ib['width']:.2f}x{ib['height']:.2f}")

    # 保存详细结果
    output_path = r'D:\Code\ExchangeNew\src\test_output\layout_coordinates.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'layout': layout,
            'zones': zones
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细坐标已保存到: {output_path}")
