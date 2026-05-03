"""
翻译系统配置文件
包含API密钥、术语表路径、排除规则等配置项

使用方法：
  1. 复制此文件为 config_local.py（不会被git跟踪）
  2. 在 config_local.py 中填入你的实际API密钥
  3. 系统会自动加载 config_local.py（如果存在），否则使用此默认配置
"""

import os
from pathlib import Path
from typing import Dict


# ==================== 基础路径配置 ====================

# 项目根目录（自动检测）
BASE_DIR = Path(__file__).parent.parent

# 输入/输出目录
INPUT_DIR = BASE_DIR / 'en-US'           # 英文原版目录
OUTPUT_DIR = BASE_DIR / 'zh-CN'          # 中文翻译输出目录
ASSETS_DIR = BASE_DIR / 'assets'         # 静态资源目录
IMAGES_DIR = BASE_DIR / 'Images'         # 图片资源目录

# ==================== 翻译引擎配置 ====================

# 默认使用的翻译后端 ('google' | 'deepl' | 'deepl-free')
DEFAULT_BACKEND = 'google'

# 并发线程数（建议4-8，避免触发API速率限制）
MAX_WORKERS = 4

# 单文件最大重试次数
MAX_RETRIES = 3

# 是否启用断点续译
ENABLE_RESUME = True

# ==================== API 密钥配置 ====================

# DeepL API 密钥（可选，不填写则使用免费版）
# 获取地址: https://www.deepl.com/pro-api
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY', '')

# Google Translate API 密钥（可选，使用免费版不需要）
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# ==================== 代理配置 ====================

# HTTP/HTTPS 代理配置
# 方式1: 自动从环境变量读取 (HTTP_PROXY / HTTPS_PROXY)
# 方式2: 手动指定代理地址，例如: {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
# 方式3: 设为 None 或 {} 表示不使用代理
PROXIES: Dict[str, str] = {
    # 'http': os.getenv('HTTP_PROXY', ''),
    # 'https': os.getenv('HTTPS_PROXY', ''),
}
# 简化：如果环境变量有设置就自动用，否则为空
if not PROXIES:
    _env_proxies = {}
    for _var, _key in [('HTTP_PROXY','http'), ('HTTPS_PROXY','https'), ('http_proxy','http'), ('https_proxy','https')]:
        _val = os.environ.get(_var)
        if _val and _key not in _env_proxies:
            _env_proxies[_key] = _val
    if _env_proxies:
        PROXIES = _env_proxies

# ==================== 后端降级配置 ====================

# 备用翻译后端（主后端连续失败时自动切换）
BACKUP_BACKEND = 'youdao'   # 可选: 'youdao', 'mymemory'

# 请求级最大重试次数（单次API调用）
API_MAX_RETRIES = 3

# 重试等待时间（秒），按顺序使用
API_RETRY_DELAYS = (2, 4, 8)

# ==================== 术语表配置 ====================

# 术语表CSV文件路径
GLOSSARY_PATH = BASE_DIR / 'translate' / 'glossary.csv'

# 是否启用术语表强制替换（True: 预替换已知术语 | False: 仅作为参考）
ENABLE_GLOSSARY_PRE_REPLACE = False

# ==================== 过滤规则配置 ====================

# 需要跳过（不翻译）的标签
SKIP_TAGS = {
    'script', 'style', 'code', 'pre', 'kbd', 
    'noscript', 'svg', 'math', 'template'
}

# 需要保护的CSS类（这些类内的文本不翻译）
PROTECT_CLASSES = {
    'variable',       # 变量名
    'code',           # 代码片段
    'literal',        # 字面值
    'formula'         # 数学公式
}

# 可翻译的标签白名单 - 仅翻译段落和一级标题
TRANSLATABLE_TAGS = {
    'p', 'h1'
}

# 不翻译的最小文本长度（字符数）
MIN_TEXT_LENGTH = 2

# 不翻译的最大单次翻译文本长度（字符数，超过此长度会分段）
MAX_TEXT_LENGTH_PER_REQUEST = 5000

# ==================== 变量名识别模式 ====================

# 变量名正则表达式（驼峰式命名）
VARIABLE_PATTERN_STRING = r'''
    \b                          # 单词边界
    [A-Z][a-z]+[A-Z][a-zA-Z]*  # 驼峰式：大写开头+小写+大写+字母
    |                           # 或者
    \b[A-Z]{2,}[a-z]*[A-Z]?\w* # 全大写缩写+小写后缀（如VavSu, AO, AI）
'''

# 单位符号正则表达式
UNIT_PATTERN_STRING = r'''
    \[\d*\.?\d*\s*              # 可选数字 + 空格
    (m³/h|ft³/min|l/s|%|s|°C|vdc|cm|bar|Pa)  # 单位列表
    \]                          # 右方括号
'''

# ==================== 版本与兼容性标记 ====================

# 保持原文的版本标记模式
VERSION_PATTERNS = [
    r'^ABT\s+\d+\.x\s+(and\s+(later|earlier))?$',
    r'^Version\s+\d+(\.\d+)*$',
    r'^Release\s+\d+(\.\d+)*$'
]

# ==================== 日志配置 ====================

LOG_DIR = BASE_DIR / 'logs'
LOG_LEVEL = 'INFO'  # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 5

# ==================== 性能优化配置 ====================

# 翻译结果缓存大小（条目数）
CACHE_SIZE = 10000

# API请求间隔（秒，避免触发速率限制）
API_REQUEST_DELAY = 0.1

# 进度保存频率（每处理多少个文件保存一次）
PROGRESS_SAVE_INTERVAL = 10

# 大文件阈值（KB），超过此大小的文件单独处理并记录日志
LARGE_FILE_THRESHOLD_KB = 50

# ==================== 质量保证配置 ====================

# 翻译后验证选项
VALIDATE_ON_SAVE = True                    # 保存时验证HTML完整性
CHECK_IMAGE_LINKS = True                   # 检查图片链接是否完整
CHECK_SCRIPT_COUNT = True                  # 检查脚本引用是否保留
VERIFY_LANG_UPDATED = True                 # 验证lang属性已更新

# 抽样检查比例（0-1，1表示检查所有文件）
SAMPLE_CHECK_RATIO = 0.05                  # 默认检查5%的文件

# ==================== 尝试加载本地配置覆盖 ====================

def load_config():
    """
    加载配置，优先使用本地配置
    
    Returns:
        dict: 合并后的配置字典
    """
    config = globals().copy()
    
    # 尝试导入本地配置
    local_config_path = Path(__file__).parent / 'config_local.py'
    if local_config_path.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config_local", local_config_path)
            local_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(local_config)
            
            # 合并本地配置（本地配置优先级更高）
            for key in dir(local_config):
                if not key.startswith('__') and key.isupper():
                    config[key] = getattr(local_config, key)
                    
            print(f"✅ 已加载本地配置: {local_config_path}")
        except Exception as e:
            print(f"⚠️ 加载本地配置失败: {e}，使用默认配置")
    
    return config


if __name__ == '__main__':
    # 测试配置加载
    config = load_config()
    print("\n" + "="*60)
    print("📋 当前翻译系统配置")
    print("="*60)
    print(f"输入目录:   {config.get('INPUT_DIR')}")
    print(f"输出目录:   {config.get('OUTPUT_DIR')}")
    print(f"翻译后端:   {config.get('DEFAULT_BACKEND')}")
    print(f"并发线程:   {config.get('MAX_WORKERS')}")
    print(f"术语表:     {'✅ 已配置' if config.get('GLOSSARY_PATH').exists() else '❌ 未找到'}")
    print(f"DeepL密钥:  {'✅ 已配置' if config.get('DEEPL_API_KEY') else '❌ 未配置'}")
    print("="*60)
