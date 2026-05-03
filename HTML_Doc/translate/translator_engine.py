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
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from abc import ABC, abstractmethod

# 尝试导入第三方库
try:
    from deep_translator import GoogleTranslator, DeeplTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    print("⚠️  deep-translator 未安装，请运行: pip install deep-translator")

import os

try:
    import requests
    from requests.exceptions import (
        ConnectionError as RequestsConnectionError,
        Timeout, SSLError, ProxyError,
        ChunkedEncodingError
    )
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


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

    @abstractmethod
    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        pass

    @abstractmethod
    def translate_batch(self, texts: List[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> List[str]:
        """批量翻译"""
        pass


class GoogleTranslationBackend(TranslationBackend):
    """
    Google Translate 后端（增强版）
    
    新增功能：
    - 代理支持（自动检测环境变量或手动配置）
    - 请求级指数退避重试（2s→4s→8s，最多3次）
    - 可重试/不可重试异常分类
    - 连续失败计数器
    """

    def __init__(self, proxies: Optional[Dict[str, str]] = None, 
                 max_retries: int = 3,
                 retry_delays: Tuple[int, ...] = (2, 4, 8)):
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

    def _resolve_proxies(self, proxies: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
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
        last_error = None
        
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
                last_error = e
                self.consecutive_failures += 1
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt] if attempt < len(self.retry_delays) else 8
                    logging.warning(
                        f"⏳ Google翻译网络错误 (第{attempt+1}/{self.max_retries}次) "
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
                        f"❌ Google翻译重试耗尽 ({self.max_retries}次) | "
                        f"最后错误: {type(e).__name__}: {str(e)[:100]}"
                    )
            
            except Exception as e:
                # 不可重试异常（如 "No translation was found"、参数错误等）
                last_error = e
                self.consecutive_failures += 1
                logging.error(f"Google翻译失败(非重试): {text[:40]}... | {type(e).__name__}: {str(e)[:100]}")
                break  # 不重试

        # 所有尝试均失败 → 返回原文
        logging.error(f"Google翻译最终失败，返回原文: {text[:50]}...")
        return text

    def translate_batch(self, texts: List[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> List[str]:
        results = []
        for text in texts:
            try:
                translated = self.translate(text, source_lang, target_lang)
                results.append(translated)
                time.sleep(0.1)  # 避免速率限制
            except Exception as e:
                logging.error(f"批量翻译失败: {text[:30]}... | {e}")
                results.append(text)
        return results


class DeepLTranslationBackend(TranslationBackend):
    """DeepL API 后端 (高质量)"""

    def __init__(self, api_key: Optional[str] = None, use_free: bool = False):
        """
        Args:
            api_key: DeepL API密钥（如果为None则使用免费版）
            use_free: 是否使用免费版API
        """
        if not DEEP_TRANSLATOR_AVAILABLE:
            raise RuntimeError("deep-translator 库未安装")

        if use_free or not api_key:
            # 使用DeepL免费版（无需API密钥，但有速率限制）
            self.translator = DeeplTranslator(source='en', target='zh', use_free_api=True)
        else:
            self.translator = DeeplTranslator(
                source='en', target='zh', 
                api_key=api_key, use_free_api=False
            )

    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        try:
            return self.translator.translate(text)
        except Exception as e:
            logging.error(f"DeepL翻译失败: {text[:30]}... | 错误: {str(e)}")
            # 回退到Google翻译
            if DEEP_TRANSLATOR_AVAILABLE:
                try:
                    fallback = GoogleTranslator(source='en', target='zh-cn')
                    return fallback.translate(text)
                except:
                    pass
            return text

    def translate_batch(self, texts: List[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> List[str]:
        results = []
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            results.append(translated)
            time.sleep(0.5)  # DeepL有较严格的速率限制
        return results


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
    
    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        try:
            # 截断过长文本
            if len(text) > 500:
                text = text[:500]
            
            url = "https://fanyi.youdao.com/translate"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://fanyi.youdao.com',
                'Referer': 'https://fanyi.youdao.com/',
            }
            
            data = {
                'i': text,
                'from': 'en',
                'to': 'zh-CHS',
                'smartresult': 'dict',
                'client': 'fanyideskweb',
                'salt': str(int(time.time() * 1000)),
                'sign': self._generate_sign(text),
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
                        return ''.join([t['tgt'] for t in lines])
            
            logging.warning(f"有道翻译响应异常: {response.status_code}")
            return text
            
        except Exception as e:
            logging.error(f"有道翻译失败: {text[:30]}... | 错误: {str(e)}")
            return text
    
    def _generate_sign(self, text: str) -> str:
        """生成有道翻译sign"""
        import hashlib
        ts = str(int(time.time() * 1000))
        salt = str(int(time.time() * 1000))
        client = 'fanyideskweb'
        secret = 'fsdssp3N4bvKKGvgEFLzHfVSzFcGadJW4h2'
        sign_str = f"client={client}&mysticTime={ts}&product=fanyideskweb&key={secret}"
        return hashlib.md5(sign_str.encode()).hexdigest()
    
    def translate_batch(self, texts: List[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> List[str]:
        results = []
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            results.append(translated)
            time.sleep(0.5)  # 有道有请求频率限制
        return results


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
    
    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        try:
            lang_pair = f"{source_lang}|zh"
            
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
            
            logging.warning(f"MyMemory翻译响应异常: {response.status_code}")
            return text
            
        except Exception as e:
            logging.error(f"MyMemory翻译失败: {text[:30]}... | 错误: {str(e)}")
            return text
    
    def translate_batch(self, texts: List[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> List[str]:
        results = []
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            results.append(translated)
            time.sleep(1)  # MyMemory有严格速率限制
        return results


# ==================== 百度翻译后端（国内可用）====================

class BaiduTranslationBackend(TranslationBackend):
    """
    百度翻译后端（推荐中国大陆用户使用）
    
    使用方式：
    1. 免费使用：无API密钥，使用公共配额（需要百度账号）
    2. API密钥：注册百度翻译开放平台获取
    """

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.use_free = not (app_id and app_secret)
        
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests库未安装，请运行: pip install requests")
        
        if self.use_free:
            logging.info("百度翻译: 使用API模式（需要app_id和app_secret）")
        else:
            logging.info(f"百度翻译: 使用API模式 (AppID: {app_id[:8]}...)")
    
    def _get_md5(self, text: str) -> str:
        """计算MD5哈希"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'zh-CN') -> str:
        """翻译单条文本"""
        try:
            if not self.app_id or not self.app_secret:
                logging.error("百度翻译需要提供app_id和app_secret")
                return text
            
            return self._translate_api(text, source_lang, target_lang)
                
        except Exception as e:
            logging.error(f"百度翻译失败: {text[:30]}... | 错误: {str(e)}")
            return text
    
    def _translate_api(self, text: str, source_lang: str, target_lang: str) -> str:
        """使用百度翻译API"""
        import random
        import urllib.parse
        
        salt = str(random.randint(32768, 65536))
        sign_str = f"{self.app_id}{text}{salt}{self.app_secret}"
        sign = self._get_md5(sign_str)
        
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        
        params = {
            'q': text,
            'from': 'en',
            'to': 'zh',
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'trans_result' in result and len(result['trans_result']) > 0:
                    return result['trans_result'][0]['dst']
                    
            logging.warning(f"百度API翻译响应异常: {response.status_code}")
            return text
            
        except Exception as e:
            logging.error(f"百度API翻译失败: {str(e)}")
            return text
    
    def translate_batch(self, texts: List[str], source_lang: str = 'en', 
                       target_lang: str = 'zh-CN') -> List[str]:
        results = []
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            results.append(translated)
            time.sleep(0.3)
        return results


# ==================== 核心翻译引擎（优化版）====================

class TranslatorEngine:
    """
    主翻译引擎（优化版）
    
    功能：
    - 多后端管理
    - 术语表加载与优先本地翻译
    - 单位符号保护（不翻译）
    - 专有名词/品牌保护（不翻译）
    - 变量名保护与恢复
    - BACnet对象类型保护
    - 枚举值保护
    - 文本预处理与优化
    - 翻译结果缓存
    """

    # ==================== 不翻译的单位和符号列表 ====================
    
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

    def __init__(self, backend: TranslationBackend, glossary_path: Optional[Path] = None):
        """
        初始化翻译引擎
        
        Args:
            backend: 翻译后端实例
            glossary_path: 术语表CSV文件路径
        """
        self.backend = backend
        self.glossary: Dict[str, str] = {}
        self.glossary_exact: Dict[str, str] = {}  # 大小写敏感精确匹配
        self.cache: Dict[str, str] = {}
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

        # ========== 保护正则模式 ==========
        
        # 变量名保护模式（严格版：仅匹配真正的技术变量名）
        # 规则：
        # 1. 驼峰式且含2+大写: VavSuSpAirFl, CetAirFlTck11, RoomPressurization
        # 2. 全大写缩写+后缀: ACnfVal, APrcVal, BCalcVal
        # 3. 全大写缩写+数字: QMX3.P87, AI01, RDG20KN
        self.variable_pattern = re.compile(
            r'(?:^|(?<=[a-z]))[A-Z][a-z]+[A-Z][a-zA-Z0-9]*\b|'   # 驼峰式(前面无大写或行首)
            r'[A-Z]{2,}[A-Z]?[a-z0-9]*\b|'                # 多大写开头(缩写)
            r'[A-Z]{2,}\d+[.\d]*\b|'                     # 缩写+数字
            r'[A-Z][A-Z][0-9]+\.[0-9]+\b'               # 版本式如 DXR2.E09
        )
        
        # URL链接保护模式
        self.url_pattern = re.compile(
            r'https?://[^\s<>"\'\)\]]+|'
            r'www\.[^\s<>"\'\)\]]+|'
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|'
            r'ftp://[^\s<>"\'\)\]]+'
        )
        
        # 文件路径保护模式（仅匹配真正的文件路径）
        # 必须包含路径分隔符 / 或 \ 或盘符:
        self.filepath_pattern = re.compile(
            r'(?:[A-Za-z]:[/\\]|[/\\])[a-zA-Z0-9_./\\-]+'
        )
        
        # 版本号和技术标识符
        self.version_pattern = re.compile(
            r'\bv?\d+\.\d+\.\d+\b|'
            r'\b\d+\.\d+\b'
        )
        
        # 构建单位保护正则（简化版：匹配裸露单位）
        # 使用单词边界匹配独立出现的单位
        self.unit_pattern = None  # 延迟构建，在需要时按需创建
        
        # 构建单位带方括号格式保护 [100 m³/h] 或 [m³/h]
        bracket_units = [re.escape(u) for u in self.UNITS_LIST if len(u) <= 10]
        self.unit_bracket_pattern = re.compile(
            r'\[\d*\.?\d*\s*(?:' + '|'.join(bracket_units[:25]) + r')\]',
            re.IGNORECASE
        )
        
        # 构建专有名词保护正则
        proper_nouns_sorted = sorted(self.PROPER_NOUNS, key=len, reverse=True)
        self.proper_noun_pattern = re.compile(
            '|'.join(re.escape(p) for p in proper_nouns_sorted)
        )
        
        # 构建 BACnet 对象类型保护正则
        bacnet_types_sorted = sorted(list(self.BACNET_TYPES), key=len, reverse=True)
        self.bacnet_type_pattern = re.compile(
            r'\b(?:' + '|'.join(re.escape(t) for t in bacnet_types_sorted) + r')\b'
        )

    def _load_glossary(self, path: Path) -> None:
        """
        加载CSV格式术语表（增强版：支持精确匹配和大小写匹配）
        
        加载策略：
        1. glossary: 小写键 → 中文（用于大小写不敏感匹配）
        2. glossary_exact: 原始英文 → 中文（用于精确匹配，优先级更高）
        """
        import csv
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                english_raw = row.get('English')
                chinese_raw = row.get('Chinese')
                
                if not english_raw or not chinese_raw:
                    continue
                    
                english = english_raw.strip()
                chinese = chinese_raw.strip()
                
                if not english or not chinese or english.startswith('#'):
                    continue
                
                # 小写版本（用于模糊匹配）
                self.glossary[english.lower()] = chinese
                # 精确版本（保留原始大小写）
                self.glossary_exact[english] = chinese

    def _protect_variables(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        保护文本中不需要翻译的内容
        
        保护优先级（按顺序）:
        0. 已有占位符（__VAR_XXX__/__UNT_XXX__/__PN_XXX__/__BAC_XXX__）— 防止重复保护
        1. URL/邮箱/文件路径
        2. 变量名（驼峰式）
        3. BACnet 对象类型缩写
        4. 单位符号
        5. 专有名词/品牌名
        6. 枚举值（固定代码值）
        
        Returns:
            tuple: (处理后的文本, 占位符映射表)
        """
        placeholders = {}
        protected_text = text
        counter = [0]

        def replace_var(match):
            var_name = match.group()
            placeholder = f"__VAR_{counter[0]:03d}__"
            placeholders[placeholder] = var_name
            counter[0] += 1
            return placeholder

        # 0. 预保护已有占位符（防止 __VAR_000__ 等格式干扰API翻译）
        # HTMLParser或上游已注入的占位符需先转为友好标记
        _existing_ph = re.compile(r'__(?:VAR|UNT|PN|BAC)_\d+__')
        for ph_match in set(_existing_ph.findall(protected_text)):
            friendly_ph = f"[PH{counter[0]}]"
            placeholders[friendly_ph] = ph_match  # [PH0] → __VAR_000__
            counter[0] += 1
            protected_text = protected_text.replace(ph_match, friendly_ph)

        # 1. URL/邮箱/文件路径
        for pattern in [self.url_pattern, self.filepath_pattern]:
            protected_text = pattern.sub(replace_var, protected_text)
        
        # 2. 变量名（驼峰式）
        protected_text = self.variable_pattern.sub(replace_var, protected_text)
        
        # 3. BACnet 对象类型
        bacnet_matches = self.bacnet_type_pattern.findall(protected_text)
        for m in set(bacnet_matches):
            placeholder = f"__BAC_{counter[0]:03d}__"
            placeholders[placeholder] = m
            counter[0] += 1
            protected_text = protected_text.replace(m, placeholder)
        
        # 4. 单位符号保护
        unit_matches = self.unit_bracket_pattern.findall(protected_text)
        for m in set(unit_matches):
            if m not in placeholders.values():
                placeholder = f"__UNT_{counter[0]:03d}__"
                placeholders[placeholder] = m
                counter[0] += 1
                protected_text = protected_text.replace(m, placeholder)
        
        # 裸露单位保护（使用简单正则匹配常见单位模式）
        for u in ['m³/h', 'm3/h', 'ft³/min', 'ft3/min', 'l/s', 'Pa', 'kPa', '%', '°C', '°F']:
            # 只匹配独立出现的单位（前后有数字或空格）
            unit_regex = re.compile(r'(?<=\d)\s*' + re.escape(u) + r'(?=\s|$|[)\]])|'
                                  r'(?:^|\s)' + re.escape(u) + r'(?=\s|$|\d)')
            for um in list(unit_regex.finditer(protected_text)):
                if um.group() not in placeholders.values():
                    placeholder = f"__UNT_{counter[0]:03d}__"
                    placeholders[placeholder] = um.group()
                    counter[0] += 1
                    protected_text = protected_text.replace(um.group(), placeholder)
        
        # 5. 专有名词保护
        proper_matches = self.proper_noun_pattern.findall(protected_text)
        for m in set(proper_matches):
            if len(m) >= 3 and m not in placeholders.values():
                placeholder = f"__PN_{counter[0]:03d}__"
                placeholders[placeholder] = m
                counter[0] += 1
                protected_text = re.sub(re.escape(m), placeholder, protected_text, flags=re.IGNORECASE)
        
        # 统计保护数量
        self.stats['protected_variables'] += counter[0]
        
        return protected_text, placeholders

    def _restore_variables(self, text: str, placeholders: Dict[str, str]) -> str:
        """恢复被保护的变量名"""
        restored = text
        for placeholder, var_name in placeholders.items():
            restored = restored.replace(placeholder, var_name)
        return restored

    def _apply_glossary(self, text: str) -> Tuple[str, int]:
        """
        在翻译前应用术语表（预替换已知术语）- 优化版
        
        匹配策略（按优先级）：
        1. 精确匹配：原始大小写完全一致
        2. 长短语优先匹配：按术语长度降序，使用单词边界
        3. 短词匹配：仅当作为独立单词时替换
        
        Returns:
            tuple: (处理后的文本, 匹配数)
        """
        matches = 0
        processed = text
        
        if not self.glossary and not self.glossary_exact:
            return processed, 0
        
        # ===== 第一轮：精确匹配（保留原始大小写的术语） =====
        for english, chinese in self.glossary_exact.items():
            if len(english) >= 3:  # 只匹配3字符以上的精确术语
                pattern = re.compile(r'\b' + re.escape(english) + r'\b', re.IGNORECASE)
                new_text = pattern.sub(chinese, processed)
                if new_text != processed:
                    matches += len(pattern.findall(processed))
                    processed = new_text
        
        # ===== 第二轮：长短语/复合术语匹配（长度>=5的术语） =====
        long_terms = [(k, v) for k, v in self.glossary.items() if len(k) >= 5]
        long_terms.sort(key=lambda x: len(x[0]), reverse=True)
        
        for english, chinese in long_terms:
            if english not in self.glossary_exact:  # 跳过已在精确匹配中处理的
                # 使用单词边界匹配
                pattern = re.compile(r'\b' + re.escape(english) + r'\b', re.IGNORECASE)
                new_text = pattern.sub(chinese, processed)
                if new_text != processed:
                    matches += len(pattern.findall(text))  # 基于原文计数
                    processed = new_text
        
        # ===== 第三轮：短术语匹配（仅在独立出现时） =====
        short_terms = [(k, v) for k, v in self.glossary.items() 
                        if 2 <= len(k) < 5 and k not in self.glossary_exact]
        
        for english, chinese in short_terms:
            pattern = re.compile(r'(?<![a-zA-Z])' + re.escape(english) + r'(?![a-zA-Z])', 
                               re.IGNORECASE)
            new_text = pattern.sub(chinese, processed)
            if new_text != processed:
                matches += 1
                processed = new_text

        if matches > 0:
            self.stats['glossary_matches'] += matches
            
        return processed, matches
    
    def _is_mostly_translated(self, text: str) -> bool:
        """
        检查文本是否应该跳过API调用（增强版 v2）
        
        跳过条件（满足任一即返回True）：
        1. 空文本
        2. 中文字符占比 > 60%（glossary已覆盖大部分）
        3. 占位符（__VAR__/__UNT__/__PN__/__BAC__）占比 > 50%（纯变量文本）
        4. 中英混合文本：同时含中文(≥1字)和英文(≥2字母) → API无法处理
        5. 去除占位符和中文字符后，有效英文内容 < 3字符（无可翻译内容）
        """
        if not text or not text.strip():
            return True
        
        # 条件0：纯数字+单位模式（如 "30 [s]", "100 ms", "5 V"）
        if re.match(r'^[\d\.\,\s\[\(\)]+[a-zA-Z°%‰]*\s*\]?\s*$', text.strip()):
            return True
            
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(' ', ''))
        
        if total_chars > 0:
            chinese_ratio = chinese_chars / total_chars
            
            # 条件1：中文字符比例 > 60%
            if chinese_ratio > 0.6:
                return True
            
            # 条件2：占位符密度 > 50%
            _ph_re = re.compile(r'__(?:VAR|UNT|PN|BAC)_\d+__')
            placeholders = _ph_re.findall(text)
            placeholder_chars = sum(len(p) for p in placeholders)
            
            if placeholder_chars > 0 and placeholder_chars / total_chars > 0.5:
                return True
            
            # 条件3（核心新增）：中英混合检测
            # 只要同时含有中文(≥1字)和英文字母(≥2字母)，API就无法正确处理
            # 例: "If 无 of the conditions" / "the 关联的 参数 is Ti__VAR_000__"
            has_chinese = chinese_chars >= 1
            has_english = bool(re.search(r'[a-zA-Z]{2,}', text))
            if has_chinese and has_english:
                return True
        
        # 条件4：有效英文内容极少（去除中文和占位符后检查）
        _ph_re2 = re.compile(r'__(?:VAR|UNT|PN|BAC)_\d+__')
        cleaned = _ph_re2.sub('', text)           # 去除占位符
        cleaned = re.sub(r'[\u4e00-\u9fff]', '', cleaned)  # 去除中文
        cleaned = re.sub(r'\s+', '', cleaned).strip()
        
        if len(cleaned) < 3:
            return True
        
        return False

    def _preprocess_text(self, text: str) -> str:
        """文本预处理：清理空白、标准化标点等"""
        # 合并多余空白
        processed = re.sub(r'\s+', ' ', text)
        # 保留首尾空白信息
        return processed.strip()

    def translate_text(self, text: str, protect_vars: bool = True) -> str:
        """
        翻译单个文本片段（完整优化流程 + 降级容错）
        
        优化后的翻译流程：
        1. 检查缓存
        2. 预处理文本
        3. 保护变量名/单位/专有名词/BACnet类型
        4. 应用术语表本地翻译（优先级最高）
        5. 检查是否需要API翻译（如果glossary已覆盖大部分则跳过）
        6. 调用后端API翻译剩余内容（含重试+降级）
        7. 恢复被保护内容
        8. 缓存结果
        
        Args:
            text: 原文
            protect_vars: 是否保护变量名
            
        Returns:
            str: 译文
        """
        # 检查缓存
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[text_hash]

        original_text = text

        try:
            # 预处理
            processed_text = self._preprocess_text(text)

            # 步骤1：保护不需要翻译的内容
            if protect_vars:
                processed_text, var_placeholders = self._protect_variables(processed_text)
            else:
                var_placeholders = {}

            # 步骤2：应用术语表进行本地翻译（核心优化）
            if self.glossary or self.glossary_exact:
                processed_text, glossary_matches = self._apply_glossary(processed_text)

            # 检查是否应该跳过API调用（独立于glossary匹配数）
            # 原因：纯变量文本/极短文本/混合文本 即使glossary没匹配也应跳过
            should_skip = self._is_mostly_translated(processed_text)
            
            if should_skip:
                self.stats['local_translations'] += 1
                self.stats['total_translations'] += 1
                
                # 恢复被保护的内容
                if var_placeholders:
                    processed_text = self._restore_variables(processed_text, var_placeholders)
                
                self.cache[text_hash] = processed_text
                return processed_text

            # 步骤3：调用翻译后端处理剩余未翻译内容（含降级机制）
            translated = self._call_backend_with_fallback(processed_text)

            # 恢复被保护的变量名
            if protect_vars and var_placeholders:
                translated = self._restore_variables(translated, var_placeholders)

            # 后处理：确保译文不为空
            if not translated.strip():
                translated = original_text
                logging.warning(f"翻译结果为空，使用原文: {original_text[:50]}...")

            # 缓存结果
            self.cache[text_hash] = translated
            self.stats['total_translations'] += 1

            return translated

        except Exception as e:
            logging.error(f"翻译出错: {original_text[:50]}... | 错误: {e}")
            return original_text

    def _call_backend_with_fallback(self, text: str) -> str:
        """
        调用主后端翻译，失败时自动降级到备用后端
        
        降级条件：主后端连续失败 >= 3 次
        降级目标：有道翻译 (YoudaoTranslationBackend)
        降级策略：一次性使用备用后端，不永久切换
        """
        # 再次检查是否应跳过（防止降级路径将混合文本送给备用后端）
        if self._is_mostly_translated(text):
            logging.debug("跳过API调用（混合文本/已翻译）")
            return text
        
        # 检查是否需要降级（仅对支持consecutive_failures的后端生效）
        _fail_count = getattr(self.backend, 'consecutive_failures', 0)
        need_fallback = _fail_count >= 3
        
        if not need_fallback:
            translated = self.backend.translate(text)
            self.stats['api_calls'] += 1
            return translated
        
        # ===== 降级路径 =====
        logging.warning(
            f"[FALLBACK] 主后端已连续失败 {_fail_count} 次，"
            f"尝试切换备用后端..."
        )
        
        try:
            fallback_backend = YoudaoTranslationBackend()
            result = fallback_backend.translate(text)
            
            # 重置主后端失败计数（下次再试主后端）
            if hasattr(self.backend, 'consecutive_failures'):
                self.backend.consecutive_failures = 0
            
            logging.info("[FALLBACK] 备用后端翻译成功")
            self.stats['api_calls'] += 1
            return result
            
        except Exception as fb_error:
            logging.error(f"[FALLBACK] 备用后端也失败了: {fb_error}")
            # 最终回退：返回当前文本（可能是glossary部分翻译的结果）
            self.stats['api_calls'] += 1
            return text

    def translate_segments(self, segments: List[Tuple[object, str]], 
                          protect_vars: bool = True) -> Dict[str, str]:
        """
        批量翻译文本片段列表
        
        Args:
            segments: [(节点对象, 原文), ...]
            protect_vars: 是否保护变量名
            
        Returns:
            dict: {原文: 译文} 字典
        """
        translations = {}
        total = len(segments)
        
        for idx, (_, original_text) in enumerate(segments):
            if original_text and original_text not in translations:
                # 控制台输出：当前翻译的段落
                _preview = original_text.replace('\n', ' ')[:60]
                _trunc = '...' if len(original_text) > 60 else ''
                print(f"  [{idx+1}/{total}] {_preview}{_trunc}", flush=True)
                
                translated = self.translate_text(original_text, protect_vars)
                translations[original_text] = translated
                
                # 控制台输出：翻译结果（截断显示）
                _result = translated.replace('\n', ' ')[:60]
                _rt = '...' if len(translated) > 60 else ''
                mark = 'SKIP' if translated == original_text else 'DONE'
                print(f"       → [{mark}] {_result}{_rt}", flush=True)
                
        return translations

    def clear_cache(self) -> None:
        """清空翻译缓存"""
        self.cache.clear()

    def get_statistics(self) -> Dict:
        """获取翻译统计信息（增强版）"""
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'glossary_size': len(self.glossary),
            'glossary_exact_size': len(self.glossary_exact),
            'api_call_ratio': (
                f"{self.stats['api_calls'] / max(self.stats['total_translations'], 1) * 100:.1f}%"
                if self.stats['total_translations'] > 0 else "N/A"
            ),
            'local_translation_rate': (
                f"{self.stats['local_translations'] / max(self.stats['total_translations'], 1) * 100:.1f}%"
                if self.stats['total_translations'] > 0 else "N/A"
            )
        }


# ==================== 工厂函数 ====================

def create_translator(backend_type: str = 'youdao', 
                      api_key: Optional[str] = None,
                      glossary_path: Optional[Path] = None,
                      use_free_api: bool = True,
                      baidu_app_id: Optional[str] = None,
                      baidu_app_secret: Optional[str] = None,
                      proxies: Optional[Dict[str, str]] = None) -> TranslatorEngine:
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
