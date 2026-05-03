"""
文档翻译工具包 - Siemens Desigo Room Automation
用于批量翻译英文技术文档HTML为中文版本

主要模块：
  - html_parser: 智能HTML解析器（节点过滤、变量保护、文本提取）
  - translator: 多后端翻译引擎（Google/DeepL/LLM适配）
  - orchestrator: 批量调度器（并发、断点续译、进度追踪）
  - utils: 工具函数（日志、MD5校验、文件IO）

使用示例:
    from translate.orchestrator import run_translation
    
    result = run_translation(
        input_dir='./en-US',
        output_dir='./zh-CN',
        backend='google',  # 或 'deepl-free'
        max_workers=4
    )
"""

__version__ = '1.0.0'
__author__ = 'Document Translation System'
__description__ = 'Siemens Desigo Room Automation 文档批量翻译工具'

# 导出主要类和函数
from .html_parser import HTMLParser
from .translator_engine import TranslatorEngine, create_translator, test_translator
from .orchestrator import (
    TranslationOrchestrator,
    FileTask,
    TranslationProgress,
    run_translation
)
from .utils import (
    setup_logging,
    calculate_md5,
    safe_read_file,
    safe_write_file,
    format_bytes,
    format_duration
)

__all__ = [
    # 核心类
    'HTMLParser',
    'TranslatorEngine',
    'TranslationOrchestrator',
    'FileTask',
    'TranslationProgress',
    
    # 便捷函数
    'create_translator',
    'run_translation',
    'test_translator',
    
    # 工具函数
    'setup_logging',
    'calculate_md5',
    'safe_read_file',
    'safe_write_file',
    'format_bytes',
    'format_duration'
]
