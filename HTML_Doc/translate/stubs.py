"""
可选依赖的兜底类型定义 + 动态导入

当第三方库未安装时，提供最小化的兜底实现，
确保静态类型分析和 import 不会失败。
"""

from typing import Any


# ==================== deep_translator 兜底 ====================

class GoogleTranslator:  # noqa: E704
    """GoogleTranslator 兜底实现（当 deep-translator 未安装时使用）"""
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


# ==================== requests 兜底 ====================

class RequestsConnectionError(Exception): pass  # noqa: E701, E704
class Timeout(Exception): pass  # noqa: E701, E704
class SSLError(Exception): pass  # noqa: E701, E704
class ProxyError(Exception): pass  # noqa: E701, E704
class ChunkedEncodingError(Exception): pass  # noqa: E701, E704


class _Response:  # noqa: E704
    """requests.Response 兜底实现"""
    status_code: int = 0
    text: str = ''
    content: bytes = b''

    def json(self, **kwargs: object) -> Any:
        return {}


class _Session:  # noqa: E704
    """requests.Session 兜底实现"""
    proxies: dict[str, str] = {}
    verify: bool | str = True
    headers: dict[str, str] = {}

    def get(self, *a: object, **kwargs: object) -> '_Response':
        return _Response()

    def post(self, *a: object, **kwargs: object) -> '_Response':
        return _Response()


class requests:  # noqa: E001, E704
    """requests 模块兜底实现"""
    Session: type[_Session] = _Session

    @staticmethod
    def get(url: object, **kwargs: object) -> '_Response':
        return _Response()

    @staticmethod
    def post(url: object, **kwargs: object) -> '_Response':
        return _Response()


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
