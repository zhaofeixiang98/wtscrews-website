#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path

def comprehensive_fix(filepath):
    """全面修复混合语言和翻译问题"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 通用修复
    fixes = [
        # 品牌名称修复
        (r'"name": "WT Cepateners"', '"name": "WT Fasteners"'),
        (r'"name": "WT Rápidoeners"', '"name": "WT Fasteners"'),
        (r'"name": "WT 快速eners"', '"name": "WT Fasteners"'),
        (r'"name": "WT 速いeners"', '"name": "WT Fasteners"'),
        (r'"name": "WT Schnelleners"', '"name": "WT Fasteners"'),
        (r'"name": "WT Rapideeners"', '"name": "WT Fasteners"'),
        (r'"name": "WT سريعeners"', '"name": "WT Fasteners"'),
        (r'"name": "WT 빠른eners"', '"name": "WT Fasteners"'),

        # JSON-LD 中的 key 修复
        (r'"@type": "UnitHargaSpecification"', '"@type": "UnitPriceSpecification"'),
        (r'"@type": "Unit価格Specification"', '"@type": "UnitPriceSpecification"'),

        # 材料名称修复
        (r'"Carbon Baja"', '"Carbon Steel"'),
        (r'"Alloy Baja"', '"Alloy Steel"'),
        (r'"Stainless Baja 304"', '"Stainless Steel 304"'),
        (r'"Stainless Baja 316"', '"Stainless Steel 316"'),
        (r'"Carbon Acero"', '"Carbon Steel"'),
        (r'"Alloy Acero"', '"Alloy Acero"'),
        (r'"Stainless Acero 304"', '"Stainless Steel 304"'),
        (r'"Stainless Acero 316"', '"Stainless Steel 316"'),
        (r'"Carbon Stahl"', '"Carbon Steel"'),
        (r'"Alloy Stahl"', '"Alloy Steel"'),
        (r'"Stainless Stahl 304"', '"Stainless Steel 304"'),
        (r'"Stainless Stahl 316"', '"Stainless Steel 316"'),
        (r'"Carbon Acier"', '"Carbon Steel"'),
        (r'"Alloy Acier"', '"Alloy Steel"'),
        (r'"Stainless Acier 304"', '"Stainless Steel 304"'),
        (r'"Stainless Acier 316"', '"Stainless Steel 316"'),
        (r'"Carbon 鋼"', '"Carbon Steel"'),
        (r'"Alloy 鋼"', '"Alloy Steel"'),
        (r'"ステンレス鋼 304"', '"Stainless Steel 304"'),
        (r'"ステンレス鋼 316"', '"Stainless Steel 316"'),
        (r'"Carbon 강"', '"Carbon Steel"'),
        (r'"Alloy 강"', '"Alloy Steel"'),
        (r'"스테인리스 강 304"', '"Stainless Steel 304"'),
        (r'"스테인리스 강 316"', '"Stainless Steel 316"'),
        (r'"ستينلس فولاذ 304"', '"Stainless Steel 304"'),
        (r'"ستينلس فولاذ 316"', '"Stainless Steel 316"'),

        # PropertyValue 名称修复
        (r'"name": "标准"', '"name": "Standards"'),
        (r'"name": "等级"', '"name": "Grade"'),
        (r'"name": "尺寸 Range"', '"name": "Size Range"'),
        (r'"name": "材料"', '"name": "Material"'),
        (r'"name": "表面处理"', '"name": "Surface Finish"'),
        (r'"name": "质量保证"', '"name": "Quality Assurance"'),
        (r'"name": "Standars"', '"name": "Standards"'),
        (r'"name": "Estándares"', '"name": "Standards"'),
        (r'"name": "Normen"', '"name": "Standards"'),
        (r'"name": "Normes"', '"name": "Standards"'),
        (r'"name": "Grados"', '"name": "Grade"'),
        (r'"name": "Metrisch"', '"name": "Metric"'),
        (r'"name": "Métrico"', '"name": "Metric"'),
        (r'"name": "Métrique"', '"name": "Metric"'),
        (r'"name": "メートル法"', '"name": "Metric"'),
        (r'"name": "미터법"', '"name": "Metric"'),
        (r'"name": "متري"', '"name": "Metric"'),
        (r'"name": "قياسي"', '"name": "Standards"'),
        (r'"name": "الدرجات"', '"name": "Grade"'),
        (r'"value": "Metrik"', '"value": "Metric"'),
        (r'"value": "公制"', '"value": "Metric"'),
        (r'"value": "英制"', '"value": "Imperial"'),
        (r'"value": "インチ"', '"value": "Imperial"'),
        (r'Metrik\)', 'Metric)'),
        (r'Métrico\)', 'Metric)'),
        (r'公制\)', 'Metric)'),
        (r'英制\)', 'Imperial)'),

        # Description 文本修复
        (r'Full and partial thread', 'Full and partial thread'),
        (r'Cepat delivery', 'Fast delivery'),
        (r'Rápido delivery', 'Fast delivery'),
        (r'速い delivery', 'Fast delivery'),
        (r'Rápida delivery', 'Fast delivery'),
    ]

    for old_pattern, replacement in fixes:
        content = re.sub(old_pattern, replacement, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """主函数"""
    base_path = Path('/Users/frank/wtscrews/222/pags')

    fixed_count = 0

    # 处理所有 HTML 文件
    for html_file in base_path.rglob('*.html'):
        try:
            if comprehensive_fix(str(html_file)):
                fixed_count += 1
                rel_path = html_file.relative_to(base_path)
                print(f"✓ 修复: {rel_path}")
        except Exception as e:
            print(f"✗ 错误: {html_file} - {e}")

    print(f"\n✅ 完成！共修复 {fixed_count} 个文件")

if __name__ == '__main__':
    main()
