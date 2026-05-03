"""
翻译引擎模块 - 支持多后端翻译API适配
支持后端：
  - Google Translate (免费额度50万字符/月)
  - DeepL API (高质量，技术文档最优)
  - DeepL API Free (免费版)
  - 本地/云端LLM (DeepSeek/Qwen等)

功能：
  - 多后端自动切换
  - 术语表注入
  - 批量文本优化
  - 错误重试机制
  - 翻译缓存
"""

import re
import time
import hashlib
import logging
from typing import Any
from pathlib import Path
from abc import ABC, abstractmethod

# ==================== 可选依赖的兜底类型定义 ====================
class GoogleTranslator:  # noqa: E704
    """GoogleTranslator 兜底实现"""
    session: object = None
    source: str = ''
    target: str = ''
    def __init__(self, *a: object, **kw: object) -> None: ...
    def translate(self, text: str = '', **kwargs: object) -> str: return text

class DeeplTranslator:  # noqa: E704
    """DeeplTranslator 兜底实现"""
    session: object = None
    source: str = ''
    target: str = ''
    def __init__(self, *a: object, **kw: object) -> None: ...
    def translate(self, text: str = '', **kwargs: object) -> str: return text

class RequestsConnectionError(Exception): pass  # noqa: E701, E704
class Timeout(Exception): pass  # noqa: E701, E704
class SSLError(Exception): pass  # noqa: E701, E704
class ProxyError(Exception): pass  # noqa: E701, E704
class ChunkedEncodingError(Exception): pass  # noqa: E701, E704

class _Response:  # noqa: E704
    status_code: int = 0
    text: str = ''
    content: bytes = b''
    def json(self, **kwargs: object) -> Any: return {}

class _Session:  # noqa: E704
    proxies: dict[str, str] = {}
    verify: bool | str = True
    headers: dict[str, str] = {}
    def get(self, *a: object, **kwargs: object) -> '_Response': return _Response()
    def post(self, *a: object, **kwargs: object) -> '_Response': return _Response()

class requests:  # noqa: E001, E704
    Session: type[_Session] = _Session
    @staticmethod
    def get(url: object, **kwargs: object) -> '_Response': return _Response()
    @staticmethod
    def post(url: object, **kwargs: object) -> '_Response': return _Response()

# ==================== 尝试导入真实依赖 ====================
_deep_translator_ok: bool = False
try:
    from deep_translator import GoogleTranslator as _RealGoogleTranslator  # type: ignore[misc]  # noqa: F401
    from deep_translator import DeeplTranslator as _RealDeeplTranslator  # type: ignore[misc]  # noqa: F401
    globals()['GoogleTranslator'] = _RealGoogleTranslator
    globals()['DeeplTranslator'] = _RealDeeplTranslator
    _deep_translator_ok = True
except ImportError:
    print("⚠️  deep-translator 未安装，请运行: pip install deep-translator")

DEEP_TRANSLATOR_AVAILABLE: bool = _deep_translator_ok

import os

_requests_ok: bool = False
try:
    import requests as _real_requests  # type: ignore[no-redef]
    from requests.exceptions import (  # type: ignore[import-not-found]
        ConnectionError,
        Timeout as _RealTimeout,
        SSLError as _RealSSLError,
        ProxyError as _RealProxyError,
        ChunkedEncodingError as _RealChunkedEncodingError,
    )
    globals()['requests'] = _real_requests
    globals()['RequestsConnectionError'] = ConnectionError
    globals()['Timeout'] = _RealTimeout
    globals()['SSLError'] = _RealSSLError
    globals()['ProxyError'] = _RealProxyError
    globals()['ChunkedEncodingError'] = _RealChunkedEncodingError
    _requests_ok = True
except ImportError:
    pass

REQUESTS_AVAILABLE: bool = _requests_ok

# ==================== 可重试异常分类 ====================

RETRYABLE_EXCEPTIONS = (
    RequestsConnectionError,   # 网络连接失败
    Timeout,                   # 请求超时  
    SSLError,                  # SSL握手失败
    ProxyError,                # 代理错误
    ChunkedEncodingError,      # 传输中断 (常见于代理)
)

# 可重试的HTTP状态码
RETRYABLE_HTTP_CODES = {502, 503, 504}  # Bad Gateway / Service Unavailable / Gateway Timeout

class TranslationBackend(ABC):
    """翻译后端抽象基类"""

    consecutive_failures: int = 0

    @abstractmethod
    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        pass

    _batch_sleep_delay: float = 0.1

    def translate_batch(self, texts: list[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> list[str]:
        """批量翻译（通用实现）"""
        results = []
        for i, text in enumerate(texts):
            try:
                translated = self.translate(text, source_lang, target_lang)
                results.append(translated)
                # 最后一条不需要等待
                if i < len(texts) - 1:
                    time.sleep(self._batch_sleep_delay)
            except Exception as e:
                logging.error(f"批量翻译中第 {i+1} 项失败: {text[:30]}... | {e}")
                results.append(text)
        return results

class GoogleTranslationBackend(TranslationBackend):
    """
    Google Translate 后端（增强版）
    
    新增功能：
    - 代理支持（自动检测环境变量或手动配置）
    - 请求级指数退避重试（2s→4s→8s，最多3次）
    - 可重试/不可重试异常分类
    - 连续失败计数器
    """

    def __init__(self, proxies: dict[str, str] | None = None, 
                 max_retries: int = 3,
                 retry_delays: tuple[int, ...] = (2, 4, 8)):
        """
        Args:
            proxies: 代理配置 {'http': '...', 'https': '...'}
                     为 None 时自动从环境变量 HTTP_PROXY/HTTPS_PROXY 读取
            max_retries: 单次请求最大重试次数
            retry_delays: 每次重试的等待秒数
        """
        if not DEEP_TRANSLATOR_AVAILABLE:
            raise RuntimeError("deep-translator 库未安装")
        
        self.max_retries = max_retries
        self.retry_delays = retry_delays
        self.consecutive_failures = 0  # 连续失败计数
        
        # 解析代理配置
        self.proxies = self._resolve_proxies(proxies)
        if self.proxies:
            logging.info(f"🌐 Google后端已配置代理: {self.proxies.get('https', self.proxies.get('http'))}")
        
        # 创建带代理的session并注入到GoogleTranslator
        self.session = None
        self.translator = GoogleTranslator(source='en', target='zh-CN')
        
        # 尝试用自定义session替换translator内部的session
        if REQUESTS_AVAILABLE and self.proxies:
            try:
                self.session = requests.Session()
                self.session.proxies.update(self.proxies)
                self.session.verify = True  # 确保SSL验证开启
                # 注入session到deep_translator的GoogleTranslator
                self.translator.session = self.session
                logging.debug("✅ 已注入自定义requests session（含代理）")
            except Exception as e:
                logging.warning(f"⚠️ 注入代理session失败: {e}，将使用环境变量代理")

    def _resolve_proxies(self, proxies: dict[str, str] | None) -> dict[str, str] | None:
        """解析代理配置：优先使用传入值，其次读取环境变量"""
        if proxies:
            return proxies
        
        env_proxies = {}
        for var in ('https_proxy', 'HTTPS_PROXY', 'http_proxy', 'HTTP_PROXY'):
            val = os.environ.get(var)
            if val:
                key = 'https' if 'https' in var.lower() else 'http'
                if key not in env_proxies:
                    env_proxies[key] = val
        
        return env_proxies if env_proxies else None

    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """
        带重试机制的翻译方法
        
        重试策略：
        - 仅对网络类错误重试（ConnectionError/Timeout/SSLError/ProxyError）
        - 指数退避：第1次等2s，第2次等4s，第3次等8s
        - 非网络错误（如"No translation found"）不重试，直接返回原文
        """
        for attempt in range(self.max_retries):
            try:
                # 设置语言
                self.translator.source = source_lang.replace('en-US', 'en')
                self.translator.target = target_lang
                
                result = self.translator.translate(text)
                
                # 成功时重置连续失败计数
                self.consecutive_failures = 0
                return result
                
            except RETRYABLE_EXCEPTIONS as e:
                _ = e
                self.consecutive_failures += 1
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt] if attempt < len(self.retry_delays) else 8
                    logging.warning(
                        f"⏳ Google翻译网络错误 (第{attempt+1}/{self.max_retries}次) "  +
                        f"| {type(e).__name__}: {str(e)[:80]} | 等待{delay}s重试..."
                    )
                    time.sleep(delay)
                    
                    # 重试前重建session（解决SSL状态损坏问题）
                    if self.proxies and REQUESTS_AVAILABLE:
                        try:
                            self.session = requests.Session()
                            self.session.proxies.update(self.proxies)
                            self.translator.session = self.session
                        except Exception:
                            pass
                else:
                    logging.error(
                        f"❌ Google翻译重试耗尽 ({self.max_retries}次) | "  +
                        f"最后错误: {type(e).__name__}: {str(e)[:100]}"
                    )
            
            except Exception as e:
                # 不可重试异常（如 "No translation was found"、参数错误等）
                _ = e
                self.consecutive_failures += 1
                logging.error(f"Google翻译失败(非重试): {text[:40]}... | {type(e).__name__}: {str(e)[:100]}")
                break  # 不重试

        # 所有尝试均失败 → 返回原文
        logging.error(f"Google翻译最终失败，返回原文: {text[:50]}...")
        return text

    # 此方法已由基类 TranslationBackend 提供通用实现

class DeepLTranslationBackend(TranslationBackend):
    """DeepL API 后端 (高质量)"""
    _batch_sleep_delay: float = 0.5

    def __init__(self, api_key: str | None = None, use_free: bool = False):
        """
        Args:
            api_key: DeepL API密钥（如果为None则使用免费版）
            use_free: 是否使用免费版API
        """
        if not DEEP_TRANSLATOR_AVAILABLE:
            raise RuntimeError("deep-translator 库未安装")

        # DeepL target 'zh' covers both zh-CN and zh-TW
        self.translator = DeeplTranslator(
            source='auto', target='zh', 
            api_key=api_key, 
            use_free_api=use_free or not api_key
        )

    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        try:
            # 更新翻译器语言设置
            self.translator.source = source_lang.replace('en-US', 'en')
            # DeepL target 'zh' is sufficient for Chinese Simplified
            self.translator.target = 'zh' if 'zh' in target_lang else target_lang

            return self.translator.translate(text)
        except Exception as e:
            logging.error(f"DeepL翻译失败: {text[:30]}... | 错误: {str(e)}")
            # 回退到Google翻译
            if DEEP_TRANSLATOR_AVAILABLE:
                try:
                    fallback = GoogleTranslator(source=source_lang, target=target_lang)
                    return fallback.translate(text)
                except Exception as fallback_e:
                    logging.error(f"DeepL后备Google翻译也失败: {fallback_e}")
                    pass
            return text

# ==================== 有道翻译后端（国内可用）====================

class YoudaoTranslationBackend(TranslationBackend):
    """
    有道翻译后端（推荐中国大陆用户使用）
    
    特点：
    - 国内可访问，完全免费
    - 支持英文→中文翻译
    - 无需API密钥
    """

    def __init__(self):
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装，请运行: pip install requests")
        logging.info("有道翻译: 免费模式（无需API密钥）")
    
    _batch_sleep_delay: float = 0.5

    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        import random
        try:
            # 截断过长文本
            if len(text.encode('utf-8')) > 4800:
                text = text[:1600]
            
            url = "https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://fanyi.youdao.com',
                'Referer': 'https://fanyi.youdao.com/',
                'Cookie': 'OUTFOX_SEARCH_USER_ID=-123456789@10.108.160.19' # 伪造一个Cookie
            }
            
            # 适配语言代码
            from_lang = source_lang.replace('en-US', 'en')
            to_lang = 'zh-CHS' if 'zh' in target_lang else target_lang

            lts = str(int(time.time() * 1000))
            salt = lts + str(random.randint(0, 9))
            sign_str = f"client=fanyideskweb&mysticTime={lts}&product=fanyideskweb&key=fsdssp3N4bvKKGvgEFLzHfVSzFcGadJW4h2"
            sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

            data = {
                'i': text,
                'from': from_lang,
                'to': to_lang,
                'smartresult': 'dict',
                'client': 'fanyideskweb',
                'salt': salt,
                'sign': sign,
                'lts': lts,
                'bv': hashlib.md5(headers['User-Agent'].encode('utf-8')).hexdigest(),
                'doctype': 'json',
                'version': '2.1',
                'keyfrom': 'fanyi.web',
                'action': 'FY_BY_REALTlME'
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errorCode') == 0 and 'translateResult' in result:
                    translations = result['translateResult']
                    if translations and len(translations) > 0:
                        lines = translations[0]
                        if isinstance(lines, list):
                            return ''.join([t.get('tgt', '') if isinstance(t, dict) else str(t) for t in lines])
                        else:
                            # 如果 lines 不是列表，直接返回
                            return str(lines)
                elif result.get('errorCode') != 0:
                    logging.warning(f"有道翻译API错误: errorCode={result.get('errorCode')}")
                    return text
            
            logging.warning(f"有道翻译响应异常: {response.status_code} | {response.text}")
            return text
            
        except Exception as e:
            logging.error(f"有道翻译失败: {text[:30]}... | 错误: {str(e)}")
            return text
    
    def _generate_sign(self, text: str) -> str:
        """(已废弃) 生成有道翻译sign。新的实现在 translate 方法中。"""
        return ""

# ==================== MyMemory免费翻译后端 ======================

class MyMemoryTranslationBackend(TranslationBackend):
    """
    MyMemory翻译后端（完全免费，无需API密钥）
    
    特点：
    - 完全免费
    - 无需注册
    - 支持100+语言
    - 每日免费额度1000词
    """

    def __init__(self):
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装，请运行: pip install requests")
        logging.info("MyMemory翻译: 免费模式（每日1000词）")
    
    _batch_sleep_delay: float = 1.0

    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        try:
            from_lang = source_lang.split('-')[0]
            to_lang = target_lang.split('-')[0]
            lang_pair = f"{from_lang}|{to_lang}"
            
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': lang_pair
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('responseStatus') == 200:
                    return result['responseData']['translatedText']
                else:
                    logging.warning(f"MyMemory翻译API错误: {result.get('responseDetails')}")
            else:
                logging.warning(f"MyMemory翻译响应异常: {response.status_code}")

            return text
            
        except Exception as e:
            logging.error(f"MyMemory翻译失败: {text[:30]}... | 错误: {str(e)}")
            return text

# ==================== 百度翻译后端（国内可用）====================

class BaiduTranslationBackend(TranslationBackend):
    """
    百度翻译后端（推荐中国大陆用户使用）
    
    使用方式：
    1. 免费使用：无API密钥，使用公共配额（需要百度账号）
    2. API密钥：注册百度翻译开放平台获取
    """

    _batch_sleep_delay: float = 0.2

    def __init__(self, app_id: str | None = None, app_secret: str | None = None):
        if not (app_id and app_secret):
            raise ValueError("百度翻译后端必须提供 app_id 和 app_secret")
        
        self.app_id = app_id
        self.app_secret = app_secret
        
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装，请运行: pip install requests")
        
        logging.info(f"百度翻译: 使用API模式 (AppID: {app_id[:8]}...)")
    
    def _get_md5(self, text: str) -> str:
        """计算MD5哈希"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        try:
            return self._translate_api(text, source_lang, target_lang)
        except Exception as e:
            logging.error(f"百度翻译失败: {text[:30]}... | 错误: {str(e)}")
            return text
    
    def _translate_api(self, text: str, source_lang: str, target_lang: str) -> str:
        """使用百度翻译API"""
        import random
        
        from_lang = source_lang.replace('en-US', 'en')
        to_lang = 'zh' if 'zh' in target_lang else target_lang

        salt = str(random.randint(32768, 65536))
        sign_str = f"{self.app_id}{text}{salt}{self.app_secret}"
        sign = self._get_md5(sign_str)
        
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        
        params = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'trans_result' in result and result['trans_result']:
                    return result['trans_result'][0]['dst']
                elif 'error_code' in result:
                    logging.error(f"百度API错误: {result['error_code']} - {result.get('error_msg')}")
            else:
                logging.warning(f"百度API翻译响应异常: {response.status_code}")

            return text
            
        except Exception as e:
            logging.error(f"百度API翻译失败: {str(e)}")
            return text
    
    def translate_batch(self, texts: list[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> list[str]:
        results = []
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            results.append(translated)
            time.sleep(0.3)
        return results

# ==================== 核心翻译引擎（优化版）====================
class TranslatorEngine:
    """翻译引擎高级封装"""

    def __init__(self, backend: TranslationBackend, glossary_path: Path | None = None):
        """
        Args:
            backend: 使用的翻译后端实例
            glossary_path: 术语表文件路径 (CSV格式)
        """
        self.translator = Translator(backend, glossary_path)

    def translate_text(self, text: str, protect_vars: bool = True) -> str:
        """
        翻译单条文本（带变量保护）
        
        Args:
            text: 待翻译文本
            protect_vars: 是否启用变量保护
        
        Returns:
            str: 翻译后的文本
        """
        return self.translator.translate_text(text, protect_vars)

    def translate_segments(self, segments: list) -> list:
        """
        批量翻译文本片段（带进度条）
        
        Args:
            segments: 待翻译的文本片段列表
            
        Returns:
            list: 翻译后的文本片段列表
        """
        return self.translator.translate_segments(segments)

    def get_statistics(self) -> dict:
        """获取翻译统计信息"""
        # 返回完整统计信息，包括术语表规模统计。
        stats = dict(self.translator.stats)
        stats['glossary_size'] = len(self.translator.glossary)
        stats['glossary_exact_size'] = len(self.translator.glossary_exact)
        return stats

    def __getattr__(self, name: str) -> Any:
        """
        属性代理，用于访问内部Translator实例的常量。
        例如，访问 engine.UNITS_LIST 会被代理到 engine.translator.UNITS_LIST
        """
        if hasattr(self.translator, name):
            return getattr(self.translator, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

class Translator:
    """
    核心翻译引擎 - 整合后端、缓存、术语表和文本保护
    """
    
    # ==================== 类级常量和术语列表 ====================
    
    # 物理单位（完整列表，覆盖 HVAC/BACnet 领域）
    UNITS_LIST = [
        # 流量单位
        'm³/h', 'm3/h', 'ft³/min', 'ft3/min', 'l/s', 'L/s', 'm³/s', 'm3/s',
        'CFM', 'GPM', 'LPM',
        # 压力单位
        'Pa', 'kPa', 'MPa', 'bar', 'mbar', 'psi', 'inH2O', 'mmH2O', 'inHg',
        # 温度单位
        '°C', '°F', 'K', 'Celsius', 'Fahrenheit', 'Kelvin',
        # 时间单位
        's', 'min', 'h', 'hr', 'ms', 'μs', 'sec',
        # 长度单位
        'm', 'cm', 'mm', 'km', 'ft', 'in', 'yd', 'mi', 'μm',
        # 面积单位
        'm²', 'm2', 'ft²', 'ft2', 'cm²', 'cm2', 'mm²', 'mm2',
        # 功率/能量单位
        'W', 'kW', 'MW', 'kWh', 'MWh', 'BTU', 'kJ', 'MJ', 'GJ',
        # 百分比/比例
        '%', 'ppm', 'ppb', 'dB', 'dB(A)',
        # 频率单位
        'Hz', 'kHz', 'MHz', 'rpm',
        # 电压单位
        'V', 'mV', 'kV', 'VDC', 'VAC',
        # 电流单位
        'A', 'mA', 'kA',
        # 其他常见单位
        'kg', 'g', 'mg', 't', 'lb', 'oz',
        'bits', 'bytes', 'KB', 'MB', 'GB', 'TB',
        'bar', 'deg', 'rad', 'lux', 'lx',
    ]
    
    # 不翻译的专有名词/品牌/产品名称
    PROPER_NOUNS = [
        # Siemens 产品线
        'Desigo Room Automation', 'Desigo CC', 'Desigo RA', 'ABT Site',
        'SCHEMA ST4', 'Bootstrap', 'jQuery', 'OpenIconic',
        'Siemens Schweiz AG', 'Siemens AG',
        # 协议标准
        'BACnet', 'Modbus RTU', 'Modbus TCP', 'KNX', 'DALI', 'DALI-2',
        'MS/TP', 'BACnet/IP', 'BACnet/SC', 'IEEE 802.1X', 'IEC 62386-209',
        'PL-Link', 'SCOM',
        # 产品型号前缀
        'DXR2', 'DXP2', 'PXC3', 'QMX3', 'QMX2', 'APS', 'OAVS',
        'RDG20', 'RDG26', 'UP258D', 'AQR257',
        # 软件版本标记
        'ABT', 'HTML', 'CSS', 'JavaScript', 'JSON', 'XML', 'CSV',
        # 实验室设备术语
        'ODP', 'SOAM', 'F-COM',
    ]
    
    # BACnet 对象类型缩写（保持原文不翻译）
    BACNET_TYPES = {
        'AI', 'AO', 'AV', 'BI', 'BO', 'BV', 'MI', 'MO', 'MV', 'MSCV', 'MSO', 'MSI',
        'ACnfVal', 'ACalcVal', 'APrcVal', 'BPrcVal', 'MPrcVal', 'SPrcVal',
        'BCalcVal', 'BTrgVal', 'MTrigVal', 'UCnfVal', 'ColView', 'FtrSel',
        'GrpMaster', 'GrpMember',
    }
    
    # 常见枚举值（保持英文，这些在代码中是固定值）
    ENUM_VALUES = [
        'On', 'Off', 'Auto', 'Manual', 'True', 'False', 'Yes', 'No',
        'Active', 'Inactive', 'Enabled', 'Disabled', 'Ready', 'Busy',
        'Normal', 'Warning', 'Alarm', 'Fault', 'Error',
        'Open', 'Closed', 'Locked', 'Unlocked',
        'High', 'Low', 'Max', 'Min', 'Maximum', 'Minimum',
        'Heating', 'Cooling', 'Ventilation', 'Protection',
        'Comfort', 'Economy', 'Pre-Comfort', 'Standby',
        'Occupied', 'Unoccupied', 'Present', 'Absent',
        'Positive', 'Negative', 'Neutral',
        'Day', 'Night', 'Schedule', 'Override',
        'Hold', 'Zero', 'None',
        'OK', 'N/A', 'NaN',
        'Input', 'Output', 'Internal', 'External',
        'Supply', 'Extract', 'Return', 'Exhaust', 'Outside',
        'Setpoint', 'Actual', 'Measured', 'Calculated',
        'Primary', 'Secondary', 'Master', 'Slave',
        'Local', 'Remote', 'Global',
        'Start', 'Stop', 'Reset', 'Cancel',
        'Success', 'Failure', 'Pending', 'Running', 'Completed',
    ]
    
    # ==================== 类级正则表达式（预编译以提高性能） ====================
    
    # 变量名保护模式
    VARIABLE_PATTERN = re.compile(
        r'(?:^|(?<=[a-z]))[A-Z][a-z]+[A-Z][a-zA-Z0-9]*\b|'   # 驼峰式
        r'[A-Z]{2,}[A-Z]?[a-z0-9]*\b|'                # 多大写开头(缩写)
        r'[A-Z]{2,}\d+[.\d]*\b|'                     # 缩写+数字
        r'[A-Z][A-Z][0-9]+\.[0-9]+\b'               # 版本式如 DXR2.E09
    )
    
    # URL/邮箱/文件路径保护模式
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"\'\)\]]+|'
        r'www\.[^\s<>"\'\)\]]+|'
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|'
        r'ftp://[^\s<>"\'\)\]]+'
    )
    FILEPATH_PATTERN = re.compile(
        r'(?:[A-Za-z]:[/\\]|[/\\])[a-zA-Z0-9_./\\-]+'
    )
    
    # 版本号
    VERSION_PATTERN = re.compile(
        r'\bv?\d+\.\d+\.\d+\b|\b\d+\.\d+\b'
    )

    def __init__(self, backend: TranslationBackend, glossary_path: Path | None = None):
        """
        初始化翻译引擎
        
        Args:
            backend: 翻译后端实例
            glossary_path: 术语表CSV文件路径
        """
        self.backend = backend
        self.glossary: dict[str, str] = {}
        self.glossary_exact: dict[str, str] = {}
        self.cache: dict[str, str] = {}
        self.stats = {
            'total_translations': 0,
            'cache_hits': 0,
            'glossary_matches': 0,
            'protected_variables': 0,
            'protected_units': 0,
            'protected_proper_nouns': 0,
            'api_calls': 0,
            'local_translations': 0,
        }

        # 加载术语表
        if glossary_path and glossary_path.exists():
            self._load_glossary(glossary_path)
            logging.info(f"✅ 已加载术语表: {len(self.glossary)} 条术语 (精确: {len(self.glossary_exact)})")

        # 动态构建的正则表达式（依赖于列表内容）
        # 单位带方括号格式保护
        bracket_units = [re.escape(u) for u in self.UNITS_LIST if len(u) <= 10]
        self.unit_bracket_pattern = re.compile(
            r'\[\d*\.?\d*\s*(?:' + '|'.join(bracket_units[:25]) + r')\]',
            re.IGNORECASE
        )
        
        # 专有名词保护
        proper_nouns_sorted = sorted(self.PROPER_NOUNS, key=len, reverse=True)
        self.proper_noun_pattern = re.compile(
            '|'.join(re.escape(p) for p in proper_nouns_sorted)
        )
        
        # BACnet 对象类型保护
        bacnet_types_sorted = sorted(list(self.BACNET_TYPES), key=len, reverse=True)
        self.bacnet_type_pattern = re.compile(
            r'\b(?:' + '|'.join(re.escape(t) for t in bacnet_types_sorted) + r')\b'
        )
        
        # 延迟构建的单位正则
        self.unit_pattern = None

    def _load_glossary(self, file_path: Path):
        """从CSV文件加载术语表"""
        import csv
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as infile:
                reader = csv.reader(infile)
                next(reader, None)  # 跳过表头
                for row in reader:
                    if len(row) >= 2 and row[0] and row[1]:
                        source, target = row[0].strip(), row[1].strip()
                        # 精确匹配的术语
                        if len(row) > 2 and row[2].strip().lower() == 'exact':
                            self.glossary_exact[source] = target
                        else:
                            self.glossary[source.lower()] = target
        except Exception as e:
            logging.error(f"加载术语表失败: {file_path} | {e}")

    def _build_unit_pattern(self):
        """延迟构建并缓存单位正则表达式"""
        if self.unit_pattern is None:
            # 按长度排序，优先匹配长单位
            sorted_units = sorted(self.UNITS_LIST, key=len, reverse=True)
            # 过滤掉特殊正则字符
            safe_units = [re.escape(u) for u in sorted_units]
            self.unit_pattern = re.compile(
                r'\b\d+\s*(' + '|'.join(safe_units) + r')\b',
                re.IGNORECASE
            )

    def _protect_variables(self, text: str) -> tuple[str, dict[str, str]]:
        """保护文本中的变量、URL、路径等，返回保护后的文本和变量映射"""
        protected_map: dict[str, str] = {}
        
        def replace_var(match: re.Match) -> str:
            var = match.group(0)
            if var in protected_map.values():
                return [k for k, v in protected_map.items() if v == var][0]
            
            placeholder = f"__VAR_{len(protected_map)}__"
            protected_map[placeholder] = var
            return placeholder

        protected_text = text
        
        # 1. URL/邮箱/文件路径
        for pattern in [self.URL_PATTERN, self.FILEPATH_PATTERN]:
            protected_text = pattern.sub(replace_var, protected_text)
        
        # 2. 变量名（驼峰式）
        protected_text = self.VARIABLE_PATTERN.sub(replace_var, protected_text)
        
        # 3. 版本号
        protected_text = self.VERSION_PATTERN.sub(replace_var, protected_text)
        
        # 4. 专有名词
        protected_text = self.proper_noun_pattern.sub(replace_var, protected_text)
        
        # 5. BACnet 对象类型
        protected_text = self.bacnet_type_pattern.sub(replace_var, protected_text)
        
        # 6. 带数字的单位
        self._build_unit_pattern()
        if self.unit_pattern:
            protected_text = self.unit_pattern.sub(replace_var, protected_text)
            
        # 7. 带方括号的单位
        protected_text = self.unit_bracket_pattern.sub(replace_var, protected_text)

        self.stats['protected_variables'] += len(protected_map)
        return protected_text, protected_map

    def _restore_variables(self, text: str, protected_map: dict[str, str]) -> str:
        """将占位符恢复为原始变量"""
        for placeholder, original_var in protected_map.items():
            text = text.replace(placeholder, original_var)
        return text

    def translate_text(self, text: str, protect_vars: bool = True) -> str:
        """
        翻译单个文本片段，包含所有处理逻辑
        """
        self.stats['total_translations'] += 1
        
        # 1. 检查缓存
        if text in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[text]
            
        # 2. 检查精确术语表
        if text in self.glossary_exact:
            self.stats['glossary_matches'] += 1
            return self.glossary_exact[text]

        # 3. 变量保护
        protected_text, protected_map = self._protect_variables(text) if protect_vars else (text, {})
        
        # 4. 翻译核心逻辑
        if protected_text.strip():
            translated_protected_text = self.backend.translate(protected_text)
            self.stats['api_calls'] += 1
        else:
            translated_protected_text = protected_text # 空白或纯占位符

        # 5. 恢复变量
        final_translation = self._restore_variables(translated_protected_text, protected_map)
        
        # 6. 更新缓存
        self.cache[text] = final_translation
        
        return final_translation

    def translate_segments(self, segments: list) -> list[str]:
        """
        批量翻译文本片段列表
        
        Args:
            segments: 待翻译的文本片段列表，可以是字符串列表或(NavigableString, str)元组列表
            
        Returns:
            list[str]: 翻译后的文本片段列表
        """
        translations = []
        for segment in segments:
            if isinstance(segment, tuple):
                # 处理 (NavigableString, str) 元组
                _, text = segment
            else:
                # 处理纯字符串
                text = segment
            translations.append(self.translate_text(text))
        return translations

    def save_cache(self, cache_path: Path):
        """保存缓存到JSON文件"""
        import json
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logging.info(f"✅ 翻译缓存已保存到: {cache_path}")
        except Exception as e:
            logging.error(f"保存缓存失败: {e}")

    def load_cache(self, cache_path: Path):
        """从JSON文件加载缓存"""
        import json
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self.cache.update(json.load(f))
                logging.info(f"✅ 已从 {cache_path} 加载 {len(self.cache)} 条缓存")
            except Exception as e:
                logging.error(f"加载缓存失败: {e}")

# ==================== 工厂函数 ====================

def create_translator(backend_type: str = 'youdao', 
                      api_key: str | None = None,
                      glossary_path: Path | None = None,
                      use_free_api: bool = True,
                      baidu_app_id: str | None = None,
                      baidu_app_secret: str | None = None,
                      proxies: dict[str, str] | None = None) -> TranslatorEngine:
    """
    工厂函数：创建翻译引擎实例
    
    Args:
        backend_type: 后端类型 ('youdao', 'mymemory', 'google', 'deepl', 'deepl-free', 'baidu')
        api_key: API密钥（DeepL付费版本需要）
        glossary_path: 术语表路径
        use_free_api: 是否使用免费API
        baidu_app_id: 百度翻译AppID（可选）
        baidu_app_secret: 百度翻译AppSecret（可选）
        proxies: 代理配置 {'http': '...', 'https': '...'}（仅Google后端使用）
        
    Returns:
        TranslatorEngine: 翻译引擎实例
    """
    if backend_type == 'youdao':
        backend = YoudaoTranslationBackend()
    elif backend_type == 'mymemory':
        backend = MyMemoryTranslationBackend()
    elif backend_type == 'google':
        backend = GoogleTranslationBackend(proxies=proxies)
    elif backend_type == 'deepl-free' or (backend_type == 'deepl' and use_free_api):
        backend = DeepLTranslationBackend(use_free=True)
    elif backend_type == 'deepl':
        if not api_key:
            raise ValueError("DeepL付费版需要提供api_key参数")
        backend = DeepLTranslationBackend(api_key=api_key, use_free=False)
    elif backend_type == 'baidu':
        backend = BaiduTranslationBackend(
            app_id=baidu_app_id,
            app_secret=baidu_app_secret
        )
    else:
        raise ValueError(f"不支持的翻译后端类型: {backend_type}")

    engine = TranslatorEngine(backend, glossary_path)
    
    logging.info(f"✅ 已创建翻译引擎 | 后端: {backend_type} | 术语表: {'已加载' if glossary_path else '无'}")
    
    return engine

def test_translator():
    """测试翻译引擎"""
    from pathlib import Path
    
    print("=" * 60)
    print("翻译引擎测试")
    print("=" * 60)

    # 创建测试用例
    test_texts = [
        "Supply air VAV box, external flow control",
        "The application function controls the damper position.",
        "Maximum airflow setpoint is 100 m³/h for cooling mode.",
        "VavSuSpAirFl outputs a setpoint signal to the controller.",
        "Device mode includes Off, Control mode, Max airflow.",
        "Interlocks are internal signals that coordinate interaction.",
        "ABT 5.x and later supports this feature.",
        "<span class=\"variable\">CetVavSu11</span> connects to an external actuator."
    ]

    # 尝试创建翻译器
    try:
        translator = create_translator(
            backend_type='google',
            glossary_path=Path(__file__).parent / 'glossary.csv',
            use_free_api=True
        )

        print("\n测试翻译结果:")
        print("-" * 60)
        
        for i, text in enumerate(test_texts, 1):
            # 清理可能的HTML标签用于显示
            clean_text = re.sub(r'<[^>]+>', '', text)
            translated = translator.translate_text(clean_text)
            
            print(f"\n{i}. 原文:")
            print(f"   {clean_text}")
            print(f"   译文:")
            print(f"   {translated}")

        print("\n" + "=" * 60)
        print("统计信息:")
        print("-" * 60)
        stats = translator.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n✅ 翻译引擎测试完成！")

    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("   请运行: pip install deep-translator")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    test_translator()