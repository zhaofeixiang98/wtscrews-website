#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path

def fix_product_pages(filepath, lang_code):
    """修复产品页面中的混合语言问题"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 修复混合语言的描述文本
    # 例如："全and partial" 应该改为 "Full and partial"
    content = re.sub(r'"全and partial thread', '"Full and partial thread', content)
    content = re.sub(r"'全and partial", "'Full and partial", content)

    # 修复中文混合的 PropertyValue 名称
    # "标准" 应该是 "Standards", "等级" 应该是 "Grade", 等等
    lang_fixes = {
        # 中文修复
        'zh': {
            '"name": "标准"': '"name": "Standards"',
            '"name": "等级"': '"name": "Grade"',
            '"name": "尺寸 Range"': '"name": "Size Range"',
            '"name": "材料"': '"name": "Material"',
            '"name": "表面处理"': '"name": "Surface Finish"',
            '"name": "质量保证"': '"name": "Quality Assurance"',
            '"value": "公制"': '"value": "Metric"',
            '"value": "英制"': '"value": "Imperial"',
            '公制': 'Metric',
            '英制': 'Imperial',
        },
        # 印尼文修复
        'id': {
            '"name": "Standars"': '"name": "Standards"',
            '"name": "Grade"': '"name": "Grades"',
            '"name": "Metrik"': '"name": "Metric"',
            '"Stainless Baja 304"': '"Stainless Steel 304"',
            '"Stainless Baja 316"': '"Stainless Steel 316"',
            '"Stainless Baja"': '"Stainless Steel"',
            '"Cepat delivery"': '"Fast delivery"',
        },
        # 西班牙文修复
        'es': {
            '"name": "Estándares"': '"name": "Standards"',
            '"name": "Grados"': '"name": "Grades"',
            '"name": "Métrico"': '"name": "Metric"',
            '"Stainless Acero 304"': '"Stainless Steel 304"',
            '"Stainless Acero 316"': '"Stainless Steel 316"',
            '"Stainless Acero"': '"Stainless Steel"',
            '"Rápido delivery"': '"Fast delivery"',
        },
        # 德文修复
        'de': {
            '"name": "Normen"': '"name": "Standards"',
            '"name": "Metrisch"': '"name": "Metric"',
            '"Stainless Stahl 304"': '"Stainless Steel 304"',
            '"Stainless Stahl 316"': '"Stainless Steel 316"',
            '"Stainless Stahl"': '"Stainless Steel"',
        },
        # 法文修复
        'fr': {
            '"name": "Normes"': '"name": "Standards"',
            '"name": "Métrique"': '"name": "Metric"',
            '"Stainless Acier 304"': '"Stainless Steel 304"',
            '"Stainless Acier 316"': '"Stainless Steel 316"',
            '"Stainless Acier"': '"Stainless Steel"',
            '"Rápido delivery"': '"Fast delivery"',
        },
        # 日文修复
        'ja': {
            '"name": "標準"': '"name": "Standards"',
            '"name": "グレード"': '"name": "Grade"',
            '"name": "メートル法"': '"name": "Metric"',
            '"ステンレス鋼 304"': '"Stainless Steel 304"',
            '"ステンレス鋼 316"': '"Stainless Steel 316"',
            '"ステンレス鋼"': '"Stainless Steel"',
            '"速い delivery"': '"Fast delivery"',
        },
        # 阿拉伯文修复
        'ar': {
            '"name": "قياسي"': '"name": "Standards"',
            '"name": "الدرجات"': '"name": "Grades"',
            '"name": "متري"': '"name": "Metric"',
            '"Stainless فولاذ 304"': '"Stainless Steel 304"',
            '"Stainless فولاذ 316"': '"Stainless Steel 316"',
            '"Stainless فولاذ"': '"Stainless Steel"',
        },
        # 韩文修复
        'ko': {
            '"name": "표준"': '"name": "Standards"',
            '"name": "등급"': '"name": "Grade"',
            '"name": "미터법"': '"name": "Metric"',
            '"스테인리스 강 304"': '"Stainless Steel 304"',
            '"스테인리스 강 316"': '"Stainless Steel 316"',
            '"스테인리스 강"': '"Stainless Steel"',
        },
    }

    if lang_code in lang_fixes:
        for old, new in lang_fixes[lang_code].items():
            content = content.replace(old, new)

    # 通用修复 - 处理混合格式
    # 修复混合数组中的语言
    patterns = [
        (r'"不锈钢 304"', '"Stainless Steel 304"'),
        (r'"不锈钢 316"', '"Stainless Steel 316"'),
        (r'"碳钢"', '"Carbon Steel"'),
        (r'"合金钢"', '"Alloy Steel"'),
        (r'"热浸镀锌"', '"Hot Dip Galvanized"'),
        (r'"半自动"', '"Semi-automatic"'),
        (r'"Stainless Baja"', '"Stainless Steel"'),
        (r'"Stainless Acero"', '"Stainless Steel"'),
        (r'"Stainless Acier"', '"Stainless Steel"'),
        (r'"Stainless Stahl"', '"Stainless Steel"'),
        (r'"Stainless فولاذ"', '"Stainless Steel"'),
        (r'"ステンレス鋼"', '"Stainless Steel"'),
        (r'"스테인리스 강"', '"Stainless Steel"'),
        (r'"@type": "UnitHargaSpecification"', '"@type": "UnitPriceSpecification"'),
        (r'"@type": "UnitPrecioSpecification"', '"@type": "UnitPriceSpecification"'),
        (r'"@type": "UnitالسعرSpecification"', '"@type": "UnitPriceSpecification"'),
    ]

    for old_pattern, replacement in patterns:
        content = re.sub(old_pattern, replacement, content)

    # 保存文件
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """主函数"""
    base_path = Path('/Users/frank/wtscrews/222/pags')

    fixed_count = 0

    # 处理所有语言目录
    for lang_code in ['zh', 'id', 'ar', 'de', 'es', 'fr', 'ja', 'ko']:
        lang_dir = base_path / lang_code / 'products'
        if not lang_dir.exists():
            print(f"⚠️  目录不存在: {lang_dir}")
            continue

        print(f"\n🔄 修复产品页面 - {lang_code.upper()} 语言...")

        # 找到所有 HTML 产品文件
        for html_file in lang_dir.glob('*.html'):
            try:
                if fix_product_pages(str(html_file), lang_code):
                    fixed_count += 1
                    print(f"  ✓ 修复: {html_file.name}")
            except Exception as e:
                print(f"  ✗ 错误: {html_file.name} - {e}")

    print(f"\n✅ 完成！共修复 {fixed_count} 个产品页面")

if __name__ == '__main__':
    main()
