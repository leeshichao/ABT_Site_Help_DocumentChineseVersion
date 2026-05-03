#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译工具包启动入口
使用方式:
    python -m translate
    python -m translate --help
    python -m translate --dry-run --limit 5
"""

import sys
import os

# 确保项目根目录在sys.path中
_current_file = os.path.abspath(__file__)
_module_dir = os.path.dirname(_current_file)  # translate/
_parent_dir = os.path.dirname(_module_dir)   # zh/

if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

if _module_dir not in sys.path:
    sys.path.insert(0, _module_dir)

# 导入并运行主程序
from translate.main import main

if __name__ == '__main__':
    main()
