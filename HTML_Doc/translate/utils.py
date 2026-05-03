"""
工具函数模块
功能：
  - 日志配置
  - MD5校验
  - 文件IO操作
  - 时间戳生成
  - 编码检测与转换
"""

import hashlib
import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


def setup_logging(log_level: int = logging.INFO, 
                  log_file: Optional[Path] = None,
                  log_format: Optional[str] = None) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径（可选）
        log_format: 自定义日志格式
        
    Returns:
        Logger: 配置好的日志器
    """
    logger = logging.getLogger('DocumentTranslator')
    logger.setLevel(log_level)
    
    # 默认格式
    if log_format is None:
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(log_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件始终记录DEBUG级别
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def calculate_md5(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    计算文件的MD5哈希值（用于断点续译时的完整性校验）
    
    Args:
        file_path: 文件路径
        chunk_size: 分块读取大小（字节）
        
    Returns:
        str: MD5哈希值（32位十六进制字符串）
    """
    md5_hash = hashlib.md5()
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在（不存在则创建）
    
    Args:
        path: 目录路径
        
    Returns:
        Path: 目录路径对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    安全读取文件内容（带错误处理和编码回退）
    
    Args:
        file_path: 文件路径
        encoding: 首选编码
        
    Returns:
        str: 文件内容
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    encodings_to_try = [encoding, 'utf-8-sig', 'latin-1']
    
    for enc in encodings_to_try:
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise IOError(f"读取文件失败 [{enc}]: {path} | {e}")
    
    raise UnicodeDecodeError(f"无法解码文件: {path}", b'', 0, 1, reason='unsupported encoding')


def safe_write_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
    """
    安全写入文件内容（原子性操作）
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 编码格式
    """
    path = Path(file_path)
    
    # 确保父目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入临时文件再重命名（避免写入中断导致文件损坏）
    temp_path = path.with_suffix(path.suffix + '.tmp')
    
    try:
        with open(temp_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # 原子性重命名
        temp_path.rename(path)
        
    except Exception as e:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
        raise IOError(f"写入文件失败: {path} | {e}")


def get_timestamp(format_string: str = '%Y%m%d_%H%M%S') -> str:
    """
    获取格式化的时间戳字符串
    
    Args:
        format_string: 时间格式
        
    Returns:
        str: 格式化时间戳
    """
    return datetime.now().strftime(format_string)


def get_file_info(file_path: Union[str, Path]) -> dict:
    """
    获取文件详细信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: 文件信息字典
    """
    path = Path(file_path)
    stat = path.stat()
    
    return {
        'name': path.name,
        'size': stat.st_size,
        'size_kb': round(stat.st_size / 1024, 2),
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'extension': path.suffix.lower(),
        'md5': calculate_md5(path) if path.exists() else None
    }


def format_bytes(size_in_bytes: float) -> str:
    """
    将字节数格式化为人类可读的大小表示
    
    Args:
        size_in_bytes: 字节数
        
    Returns:
        str: 格式化大小字符串（如 "15.23 MB"）
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = size_in_bytes
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """
    将秒数格式化为易读的时长表示
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化时长字符串（如 "2h 30m 45s"）
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


def retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 1.0, 
                       backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    带指数退避的重试装饰器
    
    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        backoff_factor: 退避因子（每次延迟乘以此值）
        exceptions: 需要重试的异常类型元组
        
    Returns:
        func的返回值
    """
    last_exception = None
    delay = initial_delay
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logging.warning(f"第{attempt + 1}次尝试失败: {e} | {delay:.1f}s后重试...")
                time.sleep(delay)
                delay *= backoff_factor
    
    raise last_exception


class Timer:
    """上下文管理器计时器"""
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        return False
    
    @property
    def elapsed_str(self) -> str:
        return format_duration(self.elapsed)
