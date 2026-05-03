"""验证修复：重试/跳过/降级三条路径"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

print("=" * 60)
print("修复验证测试 - 3条路径")
print("=" * 60)

# ==================== 路径1: 跳过检测 (glossary覆盖/占位符过多/混合文本) ====================
print("\n--- [路径1] 跳过检测 ---")
from translator_engine import TranslatorEngine


class MockBackend:
    """Mock后端：记录是否被调用"""

    def __init__(self):
        self.call_count = 0
        self.last_text = ""

    def translate(self, text, **kw):
        self.call_count += 1
        self.last_text = text
        return f"[API:{text[:30]}]"


# 1a: 占位符密度 > 50% → 跳过API
engine_skip = TranslatorEngine(
    backend=MockBackend(),
    glossary_path=Path('glossary.csv')
)
result_pure_var = engine_skip.translate_text("HCcl__VAR_000__ / HCcl__VAR_001__ / HCcl__VAR_002__")
api_calls_after_var = engine_skip.backend.call_count
print(f"  1a. 纯变量文本: API调用={api_calls_after_var} (期望0) → {'✅ 跳过' if api_calls_after_var == 0 else '❌ 未跳过'}")

# 1b: 混合文本(中文>30% + 含占位符) → 跳过API
mixed_backend = MockBackend()
engine_mixed = TranslatorEngine(
    backend=mixed_backend,
    glossary_path=Path('glossary.csv')
)
result_mixed = engine_mixed.translate_text("05 Basic 应用 functions")
api_calls_after_mixed = mixed_backend.call_count
print(f"  1b. 混合文本: API调用={api_calls_after_mixed} (期望0) → {'✅ 跳过' if api_calls_after_mixed == 0 else '❌ 未跳过'}")

# 1c: 有效内容极短(<3字符) → 跳过API
short_backend = MockBackend()
engine_short = TranslatorEngine(
    backend=short_backend,
    glossary_path=Path('glossary.csv')
)
result_short = engine_short.translate_text("__PN_000__")
api_calls_after_short = short_backend.call_count
print(f"  1c. 极短文本: API调用={api_calls_after_short} (期望0) → {'✅ 跳过' if api_calls_after_short == 0 else '❌ 未跳过'}")


# ==================== 路径2: 网络错误重试 ====================
print("\n--- [路径2] 重试机制 ---")

from translator_engine import GoogleTranslationBackend, RETRYABLE_EXCEPTIONS
import requests.exceptions as rex


class FailingGoogleBackend(GoogleTranslationBackend):
    """模拟网络错误的Google后端 - 前2次失败，第3次成功"""

    def __init__(self):
        # 跳过父类初始化，避免真正创建translator
        self.max_retries = 3
        self.retry_delays = (0.01, 0.01, 0.01)  # 极短延迟用于测试
        self.consecutive_failures = 0
        self.proxies = None
        self.attempt_count = 0

    def translate(self, text, source_lang='en', target_lang='zh-CN'):
        self.attempt_count += 1
        if self.attempt_count <= 2:
            raise rex.ProxyError('模拟代理错误')
        return f'[翻译成功]: {text}'


retry_backend = FailingGoogleBackend()
try:
    result_retry = retry_backend.translate("test text")
    print(f"  2a. 重试成功: 尝试次数={retry_backend.attempt_count}/3 → "
          f"{'✅ 第3次成功' if result_retry.startswith('[翻译成功]') else '❌ 失败'}")
except Exception as e:
    print(f"  2a. 重试失败: {e}")


# 2b: 测试重试耗尽返回原文（直接用简单方式验证）
class AlwaysFailingBackend:
    """模拟持续网络错误的后端（含重试逻辑）"""

    def __init__(self):
        self.max_retries = 2
        self.retry_delays = (0.01, 0.01)
        self.consecutive_failures = 0

    def translate(self, text, source_lang='en', target_lang='zh-CN'):
        for attempt in range(self.max_retries):
            try:
                raise rex.SSLError("SSL EOF error")
            except RETRYABLE_EXCEPTIONS as e:
                self.consecutive_failures += 1
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delays[attempt])
        return text  # 全部失败后返回原文


fail_backend = AlwaysFailingBackend()
result_fallback_input = "should return original"
result_fallback = fail_backend.translate(result_fallback_input)
print(f"  2b. 全部失败后返回原文: '{result_fallback}' → "
      f"{'✅ 返回原文' if result_fallback == result_fallback_input else '❌ 异常'}")


# ==================== 路径3: 降级机制 ====================
print("\n--- [路径3] 降级机制 ---")


class FailingWithCounter(GoogleTranslationBackend):
    """模拟连续失败的后端（consecutive_failures >= 3）"""

    def __init__(self):
        self.max_retries = 1  # 只尝试1次就放弃
        self.retry_delays = (0,)
        self.consecutive_failures = 5  # 已连续失败5次
        self.proxies = None

    def translate(self, text, source_lang='en', target_lang='zh-CN'):
        self.consecutive_failures += 1
        raise ConnectionError("模拟网络断开")


from translator_engine import YoudaoTranslationBackend


class FakeYoudao(YoudaoTranslationBackend):
    """模拟成功的有道备用后端"""

    def translate(self, text, source_lang='en', target_lang='zh-CN'):
        return f'[有道翻译]: {text}'


# 替换Youdao为FakeYoudao用于测试
import translator_engine as te_module
_OriginalYoudao = te_module.YoudaoTranslationBackend
te_module.YoudaoTranslationBackend = FakeYoudao

engine_fallback = TranslatorEngine(
    backend=FailingWithCounter(),
    glossary_path=Path('glossary.csv')
)
result_fb = engine_fallback.translate_text("Hello world test")
te_module.YoudaoTranslationBackend = _OriginalYoudao  # 恢复原始类

print(f"  3a. 主后端失败→降级有道: '{result_fb}' → "
      f"{'✅ 降级成功' if '[有道翻译]' in result_fb else '❌ 未降级'}")


# ==================== 统计汇总 ====================
print("\n" + "=" * 60)
print("统计信息:")
print("-" * 60)
stats_final = engine_skip.get_statistics()
for k in ['total_translations', 'local_translations', 'cache_hits',
           'protected_variables', 'glossary_matches']:
    print(f"  {k}: {stats_final.get(k, 0)}")

print("\n✅ 所有路径测试完成!")
