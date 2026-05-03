#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档翻译系统 - 主启动程序
Siemens Desigo Room Automation 英文技术文档 → 中文批量翻译

功能：
  ✅ 批量翻译2274个HTML文件（全自动）
  ✅ 智能解析HTML结构，保护变量名和代码
  ✅ HVAC/BACnet专业术语一致性保证
  ✅ 多后端翻译支持（Google/DeepL）
  ✅ 并发处理 + 断点续译
  ✅ 进度追踪 + 详细日志

使用方法:
  # 1. 测试模式（翻译前10个文件）
  python main.py --limit 10
  
  # 2. 完整翻译（使用Google免费API）
  python main.py --backend google --workers 4
  
  # 3. 仅扫描统计（不实际翻译）
  python main.py --dry-run
  
  # 4. 使用DeepL高质量翻译
  python main.py --backend deepl-free
  
  # 5. 从断点继续之前的翻译
  python main.py --resume

作者: Document Translation System v1.0
日期: 2026-05-02
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 修复模块导入路径 - 允许从 translate/ 目录直接运行
_current_file = Path(__file__).resolve()
_module_dir = _current_file.parent  # translate/
# 添加当前目录和父目录到sys.path
if str(_module_dir) not in sys.path:
    sys.path.insert(0, str(_module_dir))
if str(_module_dir.parent) not in sys.path:
    sys.path.insert(0, str(_module_dir.parent))


def print_banner():
    """打印程序横幅"""
    banner = """
======================================================================
       Siemens Desigo Room Automation 文档翻译系统
       English to Chinese (zh-CN) Batch Translator v1.0
======================================================================
功能:
  * 智能HTML解析（变量保护/节点过滤）
  * 专业术语表（HVAC/BACnet/Siemens）
  * 多后端翻译（Google/DeepL）
  * 并发批处理（4-8线程加速）
  * 断点续译（中断恢复）
  * 质量验证（完整性检查）
======================================================================
"""
    try:
        print(banner)
    except (UnicodeEncodeError, OSError):
        # Windows控制台编码问题，使用ASCII回退
        print("="*70)
        print("Siemens Desigo Room Automation 文档翻译系统 v1.0")
        print("="*70)


def check_dependencies():
    """检查必要的依赖库是否安装"""
    missing = []
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        missing.append('beautifulsoup4')
        print("[ERROR] 缺少: beautifulsoup4")
        print("   安装: pip install beautifulsoup4")
    
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        missing.append('deep-translator')
        print("[WARNING] 缺少: deep-translator (可选，但推荐安装)")
        print("   安装: pip install deep-translator")
    
    try:
        from tqdm import tqdm
    except ImportError:
        missing.append('tqdm')
        print("[ERROR] 缺少: tqdm")
        print("   安装: pip install tqdm")
    
    if missing:
        print("\n请运行以下命令安装依赖:")
        print("  pip install beautifulsoup4 deep-translator tqdm")
        return False
    
    return True


def validate_directories(input_dir: Path, output_dir: Path) -> bool:
    """
    验证输入输出目录的有效性
    
    Returns:
        bool: 目录是否有效
    """
    # 检查输入目录
    if not input_dir.exists():
        print(f"[ERROR] 输入目录不存在: {input_dir}")
        return False
    
    # 统计HTML文件数量
    html_files = list(input_dir.glob('*.html'))
    if not html_files:
        print(f"[ERROR] 输入目录中没有找到HTML文件: {input_dir}")
        return False
    
    print(f"[OK] 输入目录有效: {input_dir}")
    print(f"[INFO] 发现 HTML 文件: {len(html_files)} 个")
    
    # 检查输出目录（不存在会自动创建）
    if output_dir.exists():
        existing = list(output_dir.glob('*.html'))
        if existing:
            print(f"✅ 输出目录已存在，包含 {len(existing)} 个已翻译文件（将启用断点续译）")
    else:
        print(f"ℹ️ 输出目录将在首次翻译时自动创建: {output_dir}")
    
    return True


def run_translation_job(args) -> dict:
    """
    执行翻译任务
    
    Args:
        args: 命令行参数
        
    Returns:
        dict: 翻译结果报告
    """
    # 导入本地模块（避免包导入路径问题）
    from translate.translator_engine import create_translator
    from translate.orchestrator import run_translation, TranslationOrchestrator
    from translate.html_parser import HTMLParser
    
    # 获取项目根目录（translate -> zh）
    _current = Path(__file__).resolve()
    base_dir = _current.parent  # translate目录
    if base_dir.name == 'translate':
        base_dir = base_dir.parent  # 向上到zh目录
    
    input_path = base_dir / args.input if args.input else (base_dir / 'en-US')
    output_path = base_dir / args.output if args.output else (base_dir / 'zh-CN')
    
    # 验证目录
    if not validate_directories(input_path, output_path):
        return {'success': False, 'error': '目录验证失败'}
    
    # 配置日志
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # --force: 强制重新翻译（清除进度和旧输出）
    if args.force:
        import shutil
        _progress_file = base_dir / '.translation_progress.json'
        _output_dir = base_dir / 'zh-CN'
        
        if _progress_file.exists():
            _progress_file.unlink()
            print(f"[FORCE] 已清除进度记录: {_progress_file.name}")
        
        if _output_dir.exists() and any(_output_dir.iterdir()):
            shutil.rmtree(_output_dir)
            _output_dir.mkdir(parents=True, exist_ok=True)
            print(f"[FORCE] 已清除旧输出目录: zh-CN/")
        
        args.no_resume = True  # force implies no-resume
    
    try:
        # 使用便捷函数或完整调度器
        if args.simple_mode:
            # 简单模式：一键启动
            # 术语表路径处理
            _glossary = None if args.no_glossary else (base_dir / 'translate' / 'glossary.csv')
            
            result = run_translation(
                input_dir=str(input_path),
                output_dir=str(output_path),
                backend=args.backend,
                max_workers=args.workers,
                limit=args.limit,
                resume=not args.no_resume,
                dry_run=args.dry_run,
                glossary_path=str(_glossary) if _glossary else ''
            )
        else:
            # 高级模式：详细控制
            # 解析代理配置
            _proxies = None
            if args.proxy:
                _proxy_url = args.proxy
                _proxies = {
                    'http': _proxy_url,
                    'https': _proxy_url
                }
            
            translator = create_translator(
                backend_type=args.backend,
                glossary_path=None if args.no_glossary else base_dir / 'translate' / 'glossary.csv',
                use_free_api=True,
                proxies=_proxies
            )
            
            orchestrator = TranslationOrchestrator(
                input_dir=input_path,
                output_dir=output_path,
                translator_engine=translator,
                max_workers=args.workers,
                max_retries=args.retries,
                resume=not args.no_resume
            )
            
            result = orchestrator.run(limit=args.limit, dry_run=args.dry_run)
        
        return {'success': True, **result}
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断翻译任务")
        print("💡 提示: 可以使用 --resume 参数从上次进度继续")
        return {'success': False, 'error': '用户中断'}
        
    except Exception as e:
        logging.error(f"❌ 翻译任务失败: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Siemens Desigo Room Automation 文档批量翻译工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --limit 10              # 测试模式：仅翻译前10个文件
  %(prog)s --dry-run               # 仅扫描统计，不实际翻译
  %(prog)s --backend youdao        # 使用有道翻译（推荐中国大陆）
  %(prog)s --backend mymemory      # 使用MyMemory翻译（免费但慢）
  %(prog)s --backend google        # 使用Google翻译（需要代理）
  %(prog)s --backend baidu         # 使用百度翻译（需要API密钥）
  %(prog)s --backend deepl-free    # 使用DeepL免费版翻译
  %(prog)s --workers 8             # 使用8个并发线程
  %(prog)s --resume                # 从断点继续翻译
        """
    )
    
    # 路径参数
    parser.add_argument('--input', '-i', 
                       help='输入目录（英文HTML），默认 ./en-US')
    parser.add_argument('--output', '-o', 
                       help='输出目录（中文HTML），默认 ./zh-CN')
    
    # 后端选择
    parser.add_argument('--backend', '-b', 
                       choices=['youdao', 'mymemory', 'google', 'deepl', 'deepl-free', 'baidu'],
                       default='youdao',
                       help='翻译后端 (default: youdao - 推荐中国大陆用户)')
    
    # 性能参数
    parser.add_argument('--workers', '-w', type=int, default=4,
                       help='并发线程数，建议4-8 (default: 4)')
    parser.add_argument('--retries', '-r', type=int, default=3,
                       help='失败重试次数 (default: 3)')
    
    # 控制参数
    parser.add_argument('--limit', '-l', type=int, 
                       help='限制处理的文件数量（用于测试）')
    parser.add_argument('--dry-run', action='store_true',
                       help='仅扫描统计，不执行翻译')
    parser.add_argument('--no-resume', action='store_true',
                       help='禁用断点续译（从头开始）')
    parser.add_argument('--force', '-f', action='store_true',
                       help='强制重新翻译：清除进度记录和旧输出，从头开始')
    parser.add_argument('--simple-mode', action='store_true', default=True,
                       help='使用简单模式（一键启动）')
    
    # 日志参数
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='日志级别 (default: INFO)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细调试信息')
    
    # 其他选项
    parser.add_argument('--no-banner', action='store_true',
                       help='不显示启动横幅')
    parser.add_argument('--check-only', action='store_true',
                       help='仅检查环境和依赖，不执行翻译')
    parser.add_argument('--proxy', '-p',
                       metavar='URL',
                       help='HTTP/HTTPS代理地址，如 http://127.0.0.1:7890 '
                            '(不指定则自动从环境变量 HTTP_PROXY/HTTPS_PROXY 读取)')
    parser.add_argument('--no-glossary', action='store_true',
                       help='禁用本地术语表翻译（glossary.csv），全部交由API翻译')
    
    return parser.parse_args()


def main():
    """主函数"""
    # 修复Windows控制台编码问题
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    args = parse_arguments()
    
    # 显示横幅
    if not args.no_banner:
        print_banner()
    
    # 详细日志模式
    if args.verbose:
        args.log_level = 'DEBUG'
    
    # 仅检查模式
    if args.check_only:
        print("[INFO] 检查依赖和环境...\n")
        deps_ok = check_dependencies()
        
        if deps_ok:
            print("\n[OK] 所有依赖已就绪，可以开始翻译！")
        else:
            print("\n[ERROR] 请先安装缺失的依赖库。")
            sys.exit(1)
        
        # 验证目录 - 使用__file__的实际路径，向上两级到达项目根目录
        _current = Path(__file__).resolve()
        base_dir = _current.parent  # translate目录
        if base_dir.name == 'translate':
            base_dir = base_dir.parent  # 向上到zh目录
        
        input_dir = base_dir / (args.input or 'en-US')
        output_dir = base_dir / (args.output or 'zh-CN')
        dir_ok = validate_directories(input_dir, output_dir)
        
        sys.exit(0 if (deps_ok and dir_ok) else 1)
    
    # 检查依赖
    if not check_dependencies():
        print("\n[ERROR] 依赖检查未通过，请先安装必要库。")
        sys.exit(1)
    
    # 显示开始信息
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[TIME] 启动时间: {timestamp}")
    print(f"[MODE] 运行模式: {'测试' if args.limit else '完整'}翻译")
    backend_names = {'youdao': '有道翻译', 'mymemory': 'MyMemory', 'google': 'Google', 'baidu': '百度', 'deepl': 'DeepL', 'deepl-free': 'DeepL免费'}
    print(f"[BACKEND] 翻译后端: {backend_names.get(args.backend, args.backend)}")
    print(f"[WORKERS] 并发线程: {args.workers}")
    print("-" * 70)
    
    # 执行翻译任务
    result = run_translation_job(args)
    
    # 输出最终结果
    print("\n" + "="*70)
    if result.get('success'):
        print("[SUCCESS] 翻译任务完成！")
        
        # 显示报告摘要
        summary = result.get('summary', {})
        perf = result.get('performance', {})
        
        print(f"\n[STATS] 成功率: {summary.get('success_rate', 0):.1f}%")
        print(f"[STATS] 已翻译: {summary.get('completed', 0)} 个文件")
        print(f"[TIME] 总耗时: {perf.get('elapsed_time_formatted', 'N/A')}")
        
    else:
        print("[ERROR] 翻译任务失败！")
        error = result.get('error', '未知错误')
        print(f"\n原因: {error}")
        sys.exit(1)
    
    print("="*70)


if __name__ == '__main__':
    main()
