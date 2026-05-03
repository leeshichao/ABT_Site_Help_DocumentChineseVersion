#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速测试脚本"""

import sys
import os

# 确保路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 修复Windows编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

print("=== 测试1: 导入模块 ===")
try:
    from translate.main import main, parse_arguments
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

print("\n=== 测试2: 解析参数 ===")
args = parse_arguments()
print(f"✅ 参数解析成功: {args}")

print("\n=== 测试3: 检查目录 ===")
from pathlib import Path
base_dir = Path(__file__).parent
input_dir = base_dir / 'en-US'
output_dir = base_dir / 'zh-CN'
print(f"输入目录: {input_dir}")
print(f"输入目录存在: {input_dir.exists()}")
print(f"输出目录: {output_dir}")
print(f"输出目录存在: {output_dir.exists()}")

if not input_dir.exists():
    print("\n⚠️ en-US 目录不存在！")
    print("请确保在正确的目录运行此脚本。")
    sys.exit(1)

print("\n=== 测试4: 扫描HTML文件 ===")
html_files = list(input_dir.glob('*.html'))[:5]
print(f"找到 {len(html_files)} 个HTML文件（显示前5个）")
for f in html_files:
    print(f"  - {f.name} ({f.stat().st_size/1024:.1f} KB)")

print("\n=== 所有测试通过！===")
print("\n使用以下命令开始翻译:")
print("  python -m translate --limit 5  # 测试翻译前5个文件")
