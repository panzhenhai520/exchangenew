# -*- coding: utf-8 -*-
"""
分析标准AMLO-1-01 PDF文件
提取所有元素的精确位置、尺寸、字体等信息
"""

import pdfplumber
import json
from pathlib import Path

def analyze_pdf(pdf_path):
    """分析PDF文件结构"""
    results = {
        'page_size': None,
        'borders': [],
        'text_elements': [],
        'lines': [],
        'rects': [],
        'chars': []
    }

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]  # 第一页

        # 页面尺寸
        results['page_size'] = {
            'width': page.width,
            'height': page.height
        }

        # 提取所有线条
        if page.lines:
            for line in page.lines:
                results['lines'].append({
                    'x0': line['x0'],
                    'y0': line['y0'],
                    'x1': line['x1'],
                    'y1': line['y1'],
                    'width': line.get('width', 0),
                    'linewidth': line.get('linewidth', 0)
                })

        # 提取所有矩形
        if page.rects:
            for rect in page.rects:
                results['rects'].append({
                    'x0': rect['x0'],
                    'y0': rect['y0'],
                    'x1': rect['x1'],
                    'y1': rect['y1'],
                    'width': rect['x1'] - rect['x0'],
                    'height': rect['y1'] - rect['y0'],
                    'linewidth': rect.get('linewidth', 0)
                })

        # 提取所有文字（按位置）
        if page.chars:
            for char in page.chars:
                results['chars'].append({
                    'text': char['text'],
                    'x0': char['x0'],
                    'y0': char['y0'],
                    'x1': char['x1'],
                    'y1': char['y1'],
                    'fontname': char.get('fontname', ''),
                    'size': char.get('size', 0)
                })

        # 提取文本块
        text = page.extract_text()
        if text:
            results['text_content'] = text

    return results

def find_borders(rects):
    """从矩形中识别三层边框"""
    # 按面积排序（面积越大越外层）
    sorted_rects = sorted(rects, key=lambda r: r['width'] * r['height'], reverse=True)

    borders = []
    for i, rect in enumerate(sorted_rects[:5]):  # 只看前5个最大的矩形
        borders.append({
            'layer': i + 1,
            'x0': rect['x0'],
            'y0': rect['y0'],
            'width': rect['width'],
            'height': rect['height'],
            'linewidth': rect['linewidth']
        })

    return borders

def group_text_by_line(chars, tolerance=2):
    """将字符按行分组"""
    if not chars:
        return []

    # 按y坐标排序
    sorted_chars = sorted(chars, key=lambda c: c['y0'])

    lines = []
    current_line = [sorted_chars[0]]
    current_y = sorted_chars[0]['y0']

    for char in sorted_chars[1:]:
        if abs(char['y0'] - current_y) <= tolerance:
            current_line.append(char)
        else:
            # 新行
            lines.append({
                'y': current_y,
                'text': ''.join([c['text'] for c in current_line]),
                'chars': current_line
            })
            current_line = [char]
            current_y = char['y0']

    # 最后一行
    if current_line:
        lines.append({
            'y': current_y,
            'text': ''.join([c['text'] for c in current_line]),
            'chars': current_line
        })

    return lines

if __name__ == '__main__':
    import sys
    import io
    # 设置UTF-8输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 标准PDF路径
    pdf_path = r'D:\Code\ExchangeNew\src\test_output\OK\รายงาน ปปง 1-01 ซื้อขายเกิน 500,000 บาท ยกเว้นเงินบาทแลก.pdf'

    print(f"分析PDF: {pdf_path}\n")

    # 分析PDF
    results = analyze_pdf(pdf_path)

    # 识别边框
    borders = find_borders(results['rects'])

    # 分组文本
    text_lines = group_text_by_line(results['chars'])

    # 输出结果
    print(f"页面尺寸: {results['page_size']['width']:.2f} x {results['page_size']['height']:.2f} 点")
    print(f"矩形数量: {len(results['rects'])}")
    print(f"线条数量: {len(results['lines'])}")
    print(f"字符数量: {len(results['chars'])}")
    print(f"\n识别的边框层:")
    for border in borders[:3]:  # 只看前3层
        print(f"  第{border['layer']}层: x={border['x0']:.2f}, y={border['y0']:.2f}, "
              f"宽={border['width']:.2f}, 高={border['height']:.2f}, 线宽={border['linewidth']:.2f}")

    print(f"\n前20行文本:")
    for i, line in enumerate(text_lines[:20]):
        print(f"  Y={line['y']:.2f}: {line['text'][:50]}")

    # 保存完整结果到JSON
    output_path = r'D:\Code\ExchangeNew\src\test_output\standard_pdf_analysis.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'page_size': results['page_size'],
            'borders': borders,
            'text_lines': text_lines[:50],  # 前50行
            'rects': results['rects'][:20],  # 前20个矩形
            'lines': results['lines'][:20]   # 前20条线
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细分析结果已保存到: {output_path}")
