"""调试glossary匹配"""
import sys
import re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from translator_engine import TranslatorEngine

class MockBackend:
    def translate(self, t, **kw): return f'[API:{t}]'
    def translate_batch(self, ts, **kw): return [self.translate(t) for t in ts]

e = TranslatorEngine(backend=MockBackend(), glossary_path=Path('glossary.csv'))

text = 'Supply air VAV box with external flow control'
print(f'Text: {text}')
print()

# 测试每个模式
patterns = {
    'variable': e.variable_pattern,
    'url': e.url_pattern,
    'filepath': e.filepath_pattern,
}

for name, pat in patterns.items():
    matches = pat.findall(text)
    print(f'{name} pattern matches: {matches}')

# 手动测试变量模式
print('\nManual test:')
test_pat = r'(?:^|(?<=[a-z]))[A-Z][a-z]+[A-Z][a-zA-Z0-9]*\b'
print(f'Supply matches: {re.findall(test_pat, text)}')
print(f'VAV matches: {re.findall(test_pat, text)}')

pat2 = r'[A-Z]{2,}[A-Z]?[a-z0-9]*\b'
print(f'VAV with pat2: {re.findall(pat2, text)}')
print(f'Supply with pat2: {re.findall(pat2, text)}')

pat3 = r'[A-Z]{2,}\d+[.\d]*\b'
print(f'DXR2.E09 with pat3: {re.findall(pat3, text)}')

# 完整保护流程
protected, ph = e._protect_variables(text)
print(f'\nProtected text: {protected}')
print(f'Placeholders ({len(ph)}):')
for k, v in list(ph.items())[:10]:
    print(f'  {k} -> {v}')
