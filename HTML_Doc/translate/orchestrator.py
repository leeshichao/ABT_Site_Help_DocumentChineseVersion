"""
批量翻译调度器模块
功能：
  - 扫描输入目录的HTML文件
  - 分批处理（按大小分级）
  - 并发控制（线程池）
  - 断点续译（JSON进度记录）
  - 进度追踪与可视化（tqdm进度条）
  - 详细日志记录
  - 错误重试机制
"""

import json
import time
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from tqdm import tqdm

from .html_parser import HTMLParser
from .translator_engine import TranslatorEngine, create_translator


@dataclass
class FileTask:
    """文件翻译任务"""
    input_path: Path
    output_path: Path
    file_size: int
    status: str = 'pending'  # pending/done/failed/skipped
    attempts: int = 0
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    segments_count: int = 0
    translated_count: int = 0


@dataclass
class TranslationProgress:
    """翻译进度跟踪"""
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    pending_files: int = 0
    total_segments: int = 0
    translated_segments: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)


class TranslationOrchestrator:
    """
    批量翻译调度器
    
    负责协调整个翻译流程：
    1. 文件扫描与任务队列生成
    2. 断点续译检查
    3. 并发执行翻译任务
    4. 进度追踪与报告
    5. 错误处理与重试
    """

    def __init__(self, 
                 input_dir: Path,
                 output_dir: Path,
                 translator_engine: TranslatorEngine,
                 max_workers: int = 4,
                 max_retries: int = 3,
                 resume: bool = True,
                 progress_file: Optional[Path] = None):
        """
        初始化调度器
        
        Args:
            input_dir: 输入目录（包含英文HTML）
            output_dir: 输出目录（存放中文HTML）
            translator_engine: 翻译引擎实例
            max_workers: 最大并发线程数（建议4-8，避免触发API限制）
            max_retries: 单文件最大重试次数
            resume: 是否启用断点续译
            progress_file: 进度记录文件路径
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.translator = translator_engine
        self.parser = HTMLParser()
        
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.resume_enabled = resume
        
        # 进度文件默认位置
        self.progress_file = progress_file or (self.output_dir.parent / '.translation_progress.json')
        
        # 任务队列
        self.tasks: Dict[str, FileTask] = {}  # filename -> FileTask
        
        # 进度统计
        self.progress = TranslationProgress()
        
        # 日志配置
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """配置日志系统"""
        log_dir = self.output_dir.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'translation_{timestamp}.log'
        
        logger = logging.getLogger('TranslationOrchestrator')
        logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        self.log_file = log_file
        return logger

    def scan_directory(self, pattern: str = '*.html') -> int:
        """
        扫描输入目录中的所有HTML文件
        
        Args:
            pattern: 文件匹配模式
            
        Returns:
            int: 发现的文件数量
        """
        self.logger.info(f"🔍 开始扫描目录: {self.input_dir}")
        
        html_files = list(self.input_dir.glob(pattern))
        
        for html_file in html_files:
            relative_name = html_file.name
            output_path = self.output_dir / html_file.name
            file_size = html_file.stat().st_size
            
            task = FileTask(
                input_path=html_file,
                output_path=output_path,
                file_size=file_size
            )
            self.tasks[relative_name] = task
        
        self.progress.total_files = len(self.tasks)
        self.progress.pending_files = len(self.tasks)
        
        self.logger.info(f"✅ 扫描完成 | 发现 {len(html_files)} 个HTML文件")
        
        # 统计文件大小分布
        sizes = [task.file_size for task in self.tasks.values()]
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            max_size = max(sizes)
            min_size = min(sizes)
            total_size = sum(sizes) / (1024 * 1024)  # MB
            self.logger.info(f"📊 文件统计 | 总大小: {total_size:.2f}MB | 平均: {avg_size:.1f}KB | 最大: {max_size/1024:.1f}KB | 最小: {min_size/1024:.1f}KB")
        
        return len(html_files)

    def load_progress(self) -> bool:
        """
        加载之前的翻译进度（断点续译）
        
        Returns:
            bool: 是否成功加载进度
        """
        if not self.resume_enabled or not self.progress_file.exists():
            return False
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                
            # 恢复已完成的任务状态
            completed_files = saved_data.get('completed_files', {})
            for filename, info in completed_files.items():
                if filename in self.tasks:
                    self.tasks[filename].status = 'done'
                    self.tasks[filename].segments_count = info.get('segments_count', 0)
                    self.tasks[filename].translated_count = info.get('translated_count', 0)
                    
            # 更新进度计数
            self.progress.completed_files = len(completed_files)
            self.progress.pending_files = self.progress.total_files - self.progress.completed_files
            
            self.logger.info(f"🔄 加载进度 | 已完成: {self.progress.completed_files} | 待处理: {self.progress.pending_files}")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 无法加载进度文件: {e}")
            return False

    def save_progress(self) -> None:
        """保存当前翻译进度到JSON文件"""
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'total_files': self.progress.total_files,
            'completed_files': {},
            'statistics': {
                'completed': self.progress.completed_files,
                'failed': self.progress.failed_files,
                'skipped': self.progress.skipped_files,
                'total_segments': self.progress.total_segments,
                'translated_segments': self.progress.translated_segments
            },
            'translator_stats': self.translator.get_statistics()
        }
        
        # 记录已完成的文件详情
        for name, task in self.tasks.items():
            if task.status == 'done':
                progress_data['completed_files'][name] = {
                    'file_size': task.file_size,
                    'segments_count': task.segments_count,
                    'translated_count': task.translated_count,
                    'processing_time': (task.end_time or 0) - (task.start_time or 0)
                }
        
        # 确保目录存在
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    def translate_single_file(self, task: FileTask) -> bool:
        """
        翻译单个文件（核心方法）
        
        Args:
            task: 文件翻译任务
            
        Returns:
            bool: 是否成功
        """
        task.attempts += 1
        task.start_time = time.time()
        
        try:
            self.logger.debug(f"📄 开始翻译: {task.input_path.name} ({task.file_size/1024:.1f}KB)")
            
            # 1. 解析HTML并提取文本
            soup, segments = self.parser.parse_file(task.input_path)
            task.segments_count = len(segments)
            
            if not segments:
                # 无需翻译的内容（可能全是代码或变量）
                task.status = 'skipped'
                task.end_time = time.time()
                self.logger.warning(f"⏭️ 跳过（无可翻译文本）: {task.input_path.name}")
                return True
            
            # 2. 批量翻译
            translations = self.translator.translate_segments(segments)
            task.translated_count = len(translations)
            
            # 3. 回填翻译结果到DOM
            replaced = self.parser.replace_translated_text(segments, translations)
            
            # 4. 更新语言属性为中文
            self.parser.update_html_lang(soup, 'zh-CN')
            
            # 5. 保存翻译后的文件
            self.parser.save_translated_file(soup, task.output_path)
            
            # 6. 更新任务状态
            task.status = 'done'
            task.end_time = time.time()
            
            # 更新全局进度
            self.progress.completed_files += 1
            self.progress.pending_files -= 1
            self.progress.total_segments += task.segments_count
            self.progress.translated_segments += task.translated_count
            
            processing_time = task.end_time - task.start_time
            self.logger.info(
                f"✅ 完成翻译: {task.input_path.name} | "
                f"片段: {task.segments_count} → {task.translated_count} | "
                f"耗时: {processing_time:.2f}s"
            )
            
            # 定期保存进度（每10个文件保存一次）
            if self.progress.completed_files % 10 == 0:
                self.save_progress()
            
            return True

        except Exception as e:
            task.error_message = str(e)
            task.status = 'failed'
            task.end_time = time.time()
            
            self.logger.error(
                f"❌ 翻译失败: {task.input_path.name} | "
                f"第{task.attempts}次尝试 | 错误: {e}"
            )
            
            # 如果还有重试机会，重新标记为pending
            if task.attempts < self.max_retries:
                task.status = 'pending'
                # 指数退避等待
                wait_time = min(2 ** task.attempts, 30)
                self.logger.info(f"⏳ 将在 {wait_time}s 后重试...")
                time.sleep(wait_time)
            
            return False

    def run(self, limit: Optional[int] = None, dry_run: bool = False) -> Dict:
        """
        执行批量翻译任务
        
        Args:
            limit: 限制处理的文件数量（用于测试）
            dry_run: 仅扫描不执行翻译
            
        Returns:
            dict: 翻译结果统计
        """
        self.progress.start_time = time.time()
        
        # 1. 扫描目录（如果尚未扫描）
        if not self.tasks:
            self.scan_directory()
        
        # 2. 加载之前的进度
        self.load_progress()
        
        # 3. 过滤待处理任务
        pending_tasks = [
            task for task in self.tasks.values() 
            if task.status == 'pending'
        ]
        
        if limit:
            pending_tasks = pending_tasks[:limit]
            self.logger.info(f"🎯 测试模式 | 限制处理前 {limit} 个文件")
        
        if not pending_tasks:
            self.logger.info("🎉 所有文件已翻译完成！")
            return self._generate_report()
        
        if dry_run:
            self.logger.info(f"🔍 Dry Run 模式 | 将处理 {len(pending_tasks)} 个文件")
            for task in pending_tasks[:10]:
                print(f"  📄 {task.input_path.name} ({task.file_size/1024:.1f}KB)")
            return {'dry_run': True, 'files_count': len(pending_tasks)}
        
        # 4. 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 5. 显示开始信息
        print("\n" + "="*70)
        print("🚀 开始批量翻译")
        print("="*70)
        print(f"📂 输入目录: {self.input_dir}")
        print(f"📂 输出目录: {self.output_dir}")
        print(f"📊 总文件数: {self.progress.total_files}")
        print(f"⏳ 待处理数: {len(pending_tasks)}")
        print(f"🔧 并发线程: {self.max_workers}")
        print(f"📝 日志文件: {self.log_file}")
        print("="*70 + "\n")
        
        # 6. 使用线程池并发执行
        failed_tasks = []
        completed_count = 0
        
        with tqdm(total=len(pending_tasks), desc="翻译进度", unit="文件") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_task = {
                    executor.submit(self.translate_single_file, task): task 
                    for task in pending_tasks
                }
                
                # 收集结果
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        success = future.result()
                        if success and task.status == 'done':
                            completed_count += 1
                        elif task.status == 'failed' and task.attempts >= self.max_retries:
                            failed_tasks.append(task)
                            self.progress.failed_files += 1
                    except Exception as e:
                        self.logger.error(f"任务异常: {task.input_path.name} | {e}")
                        failed_tasks.append(task)
                        self.progress.failed_files += 1
                    
                    pbar.update(1)
        
        # 7. 完成处理
        self.progress.end_time = time.time()
        
        # 最终保存进度
        self.save_progress()
        
        # 输出失败文件清单
        if failed_tasks:
            self.logger.error(f"\n❌ {len(failed_tasks)} 个文件翻译失败:")
            for task in failed_tasks:
                self.logger.error(f"  - {task.input_path.name}: {task.error_message}")
        
        return self._generate_report()

    def _generate_report(self) -> Dict:
        """生成最终报告"""
        elapsed_time = (self.progress.end_time or time.time()) - (self.progress.start_time or time.time())
        
        report = {
            'status': 'completed' if self.progress.failed_files == 0 else 'completed_with_errors',
            'summary': {
                'total_files': self.progress.total_files,
                'completed': self.progress.completed_files,
                'failed': self.progress.failed_files,
                'skipped': self.progress.skipped_files,
                'success_rate': (
                    (self.progress.completed_files / max(self.progress.total_files, 1)) * 100
                    if self.progress.total_files > 0 else 0
                )
            },
            'performance': {
                'elapsed_time_seconds': round(elapsed_time, 2),
                'elapsed_time_formatted': self._format_duration(elapsed_time),
                'avg_time_per_file': round(elapsed_time / max(self.progress.completed_files, 1), 2),
                'files_per_minute': round((self.progress.completed_files / max(elapsed_time, 1)) * 60, 2)
            },
            'translation_stats': {
                'total_segments': self.progress.total_segments,
                'translated_segments': self.progress.translated_segments,
                'translator_cache_hits': self.translator.stats.get('cache_hits', 0),
                'glossary_matches': self.translator.stats.get('glossary_matches', 0)
            }
        }
        
        # 打印美观的报告
        self._print_report(report)
        
        return report

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化持续时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        parts.append(f"{secs}秒")
        
        return ''.join(parts)

    def _print_report(self, report: Dict) -> None:
        """打印美化的报告"""
        print("\n" + "="*70)
        print("📊 翻译任务完成报告")
        print("="*70)
        
        summary = report['summary']
        perf = report['performance']
        trans = report['translation_stats']
        
        print(f"\n✨ 任务状态: {report['status'].upper().replace('_', ' ')}")
        print(f"\n📈 文件统计:")
        print(f"  • 总计文件:     {summary['total_files']} 个")
        print(f"  • 成功翻译:     ✅ {summary['completed']} 个 ({summary['success_rate']:.1f}%)")
        print(f"  • 失败跳过:     ❌ {summary['failed']} 个")
        print(f"  • 跳过（空）:   ⏭️ {summary['skipped']} 个")
        
        print(f"\n⚡ 性能指标:")
        print(f"  • 总耗时:       {perf['elapsed_time_formatted']}")
        print(f"  • 平均每文件:   {perf['avg_time_per_file']:.2f}s")
        print(f"  • 处理速度:     {perf['files_per_minute']:.1f} 文件/分钟")
        
        print(f"\n📝 翻译统计:")
        print(f"  • 文本片段:     {trans['total_segments']} 个")
        print(f"  • 成功翻译:     {trans['translated_segments']} 个")
        print(f"  • 缓存命中:     {trans['translator_cache_hits']} 次")
        print(f"  • 术语匹配:     {trans['glossary_matches']} 次")
        
        print(f"\n📂 输出位置: {self.output_dir.absolute()}")
        print(f"📋 进度文件: {self.progress_file.absolute()}")
        print(f"📋 日志文件: {self.log_file}")
        print("="*70 + "\n")


# ==================== 便捷启动函数 ====================

def run_translation(input_dir: str = './en-US',
                   output_dir: str = './zh-CN',
                   backend: str = 'google',
                   max_workers: int = 4,
                   limit: Optional[int] = None,
                   resume: bool = True,
                   dry_run: bool = False,
                   glossary_path: Optional[str] = None) -> Dict:
    """
    一键启动翻译任务的便捷函数
    
    Args:
        input_dir: 英文HTML目录
        output_dir: 中文输出目录
        backend: 翻译后端 ('google', 'deepl', 'deepl-free')
        max_workers: 并发线程数
        limit: 限制处理数量（测试用）
        resume: 启用断点续译
        dry_run: 仅扫描不翻译
        glossary_path: 术语表路径（None=默认glossary.csv, ""=禁用术语表）
        
    Returns:
        dict: 翻译报告
    """
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    base_dir = Path(__file__).parent
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 解析术语表路径（None→默认，""→禁用，其他→指定路径）
    if glossary_path is None:
        _glossary_path = base_dir / 'glossary.csv'
    elif glossary_path == '':
        _glossary_path = None
    else:
        _glossary_path = Path(glossary_path)
    
    # 创建翻译器
    translator = create_translator(
        backend_type=backend,
        glossary_path=_glossary_path,
        use_free_api=True
    )
    
    # 创建调度器并运行
    orchestrator = TranslationOrchestrator(
        input_dir=input_path,
        output_dir=output_path,
        translator_engine=translator,
        max_workers=max_workers,
        resume=resume
    )
    
    return orchestrator.run(limit=limit, dry_run=dry_run)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='批量HTML文档翻译工具')
    parser.add_argument('--input', '-i', default='./en-US', help='输入目录（英文HTML）')
    parser.add_argument('--output', '-o', default='./zh-CN', help='输出目录（中文HTML）')
    parser.add_argument('--backend', '-b', choices=['google', 'deepl', 'deepl-free'], 
                       default='google', help='翻译后端')
    parser.add_argument('--workers', '-w', type=int, default=4, help='并发线程数')
    parser.add_argument('--limit', '-l', type=int, default=None, help='限制处理数量（测试用）')
    parser.add_argument('--no-resume', action='store_true', help='禁用断点续译')
    parser.add_argument('--dry-run', action='store_true', help='仅扫描不翻译')
    
    args = parser.parse_args()
    
    result = run_translation(
        input_dir=args.input,
        output_dir=args.output,
        backend=args.backend,
        max_workers=args.workers,
        limit=args.limit,
        resume=not args.no_resume,
        dry_run=args.dry_run
    )
