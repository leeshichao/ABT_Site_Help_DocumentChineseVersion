"""测试优化后的翻译引擎"""
import sys
import os

# ========== 路径配置 ==========
from pathlib import Path
_BASE_DIR = Path(__file__).resolve().parent.parent  # tests -> HTML_Doc
sys.path.insert(0, str(_BASE_DIR))
os.chdir(str(_BASE_DIR))

# Windows编码修复
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 导入模块（从 translate 包）
from translate.translator_engine import TranslatorEngine

print('=' * 60)
print('优化后的翻译引擎测试')
print('=' * 60)


class MockBackend:
    """模拟后端（不实际调用API）"""
    def translate(self, text, **kw):
        return f'[API:{text}]'

    def translate_batch(self, texts, **kw):
        return [self.translate(t) for t in texts]


# 创建引擎
engine = TranslatorEngine(
    backend=MockBackend(),
    glossary_path=_BASE_DIR / 'translate' / 'glossary.csv'
)

stats = engine.get_statistics()
print(f'\n术语表加载: {stats["glossary_size"]} 条 (精确: {stats.get("glossary_exact_size", 0)})')
print(f'单位列表: {len(engine.UNITS_LIST)} 个')
print(f'专有名词: {len(engine.PROPER_NOUNS)} 个')
print(f'BACnet类型: {len(engine.BACNET_TYPES)} 个')
print(f'枚举值: {len(engine.ENUM_VALUES)} 个')


# 测试用例 - 覆盖各种场景
test_cases = [
    'Supply air VAV box with external flow control',
    'Maximum airflow setpoint is 100 m3/h for cooling mode',
    'The application function CetAirFlTck11 calculates flow setpoints',
    'Room pressurization mode can be Neutral, Positive or Negative',
    'Desigo Room Automation ABT Site V6.0 supports BACnet/SC',
    'Value: 10 [m3/h] or 0.0 [ft3/min] or 35.0 Pa',
    'ACnfVal object type with Active and Normal status',
    'Heating, Cooling, Ventilation modes are configured',
    'Fume hood sash position sensor for lab safety',
    'BACnet IP routing and MS/TP protocol',
    'DALI device type 8 for HCL lighting control',
    'QMX3.P87 operator display panel configuration',
]

print('\n' + '-' * 60)
print('翻译结果:')
print('-' * 60)

for i, text in enumerate(test_cases, 1):
    translated = engine.translate_text(text)
    
    # 简化显示
    clean = translated
    for marker in ['__VAR_', '__UNT_', '__PN_', '__BAC_']:
        idx = clean.find(marker)
        while idx >= 0:
            end = clean.find('__', idx + 5)
            if end > 0:
                orig = clean[idx:end + 2]
                clean = clean[:idx] + '[' + orig[5:] + ']' + clean[end + 2:]
            else:
                break
            idx = clean.find(marker, idx + 1)
    
    print(f'\n{i}. 原文:')
    print(f'   {text[:90]}')
    print(f'   译文:')
    print(f'   {clean[:120]}')


# 最终统计
final_stats = engine.get_statistics()
print('\n' + '=' * 60)
print('统计信息:')
print('-' * 60)
for k, v in final_stats.items():
    if not k.startswith('_'):
        print(f'  {k}: {v}')
