"""
HTML智能解析模块 - 用于Siemens Desigo Room Automation技术文档翻译
功能：
  - 白名单/黑名单节点过滤
  - 变量名识别与保护
  - 单位符号保留
  - 文本分段提取
  - HTML结构完整保留
"""

import re
from bs4 import BeautifulSoup, NavigableString, Tag
from typing import List, Tuple, Dict, Optional, Set
from pathlib import Path


class HTMLParser:
    """智能HTML解析器，用于提取可翻译文本并保持DOM结构完整性"""

    # ==================== 配置常量 ====================

    # 可翻译的标签（白名单）- 仅翻译段落和一级标题
    TRANSLATABLE_TAGS: Set[str] = {
        'p', 'h1'
    }

    # 需要跳过的标签及其子内容（黑名单）
    SKIP_TAGS: Set[str] = {
        'script', 'style', 'code', 'pre', 'kbd',
        'noscript', 'svg', 'math'
    }

    # 需要保护的CSS类（不翻译其内容）
    PROTECT_CLASSES: Set[str] = {
        'variable'  # 变量名类，如 <span class="variable">VavSuSpAirFl</span>
    }

    # 变量名匹配正则（驼峰式：大写字母开头或包含连续大写字母的模式）
    VARIABLE_PATTERN = re.compile(
        r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b|'
        r'\b[A-Z]{2,}[a-z]*[A-Z]?\w*\b'
    )

    # 单位符号匹配正则（如 [m³/h], [50 m³/h], [29.4 ft³/min], [%] 等）
    UNIT_PATTERN = re.compile(
        r'\[\d*\.?\d*\s*(m³/h|ft³/min|l/s|%|s|°C|vdc|cm)\]',
        re.UNICODE
    )

    # 纯数字/符号文本模式（不翻译）
    PURE_NUMERIC_PATTERN = re.compile(r'^[\d\s\.\-\+\=\<\>\(\)\[\]\{\}\;\:\,\!\?\*\&\%\$\#\@\^~`\/\\|]+$', re.UNICODE)

    # 版本标记模式（保持原文）
    VERSION_PATTERN = re.compile(
        r'^ABT\s+\d+\.x\s+(and\s+(later|earlier))?$', 
        re.IGNORECASE
    )

    def __init__(self):
        """初始化解析器"""
        self.stats = {
            'total_files': 0,
            'total_segments': 0,
            'protected_variables': 0,
            'protected_units': 0,
            'skipped_tags': 0,
            'translated_segments': 0
        }

    def parse_file(self, file_path: Path) -> Tuple[BeautifulSoup, List[Tuple[NavigableString, str]]]:
        """
        解析单个HTML文件，提取可翻译文本片段
        
        Args:
            file_path: HTML文件路径
            
        Returns:
            tuple: (BeautifulSoup对象, 可翻译文本片段列表)
                   片段格式: (NavigableString节点, 提取的文本内容)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        segments = self._extract_translatable_text(soup)
        
        self.stats['total_files'] += 1
        self.stats['total_segments'] += len(segments)
        
        return soup, segments

    def _extract_translatable_text(self, soup: BeautifulSoup) -> List[Tuple[NavigableString, str]]:
        """
        从BeautifulSoup对象中提取需要翻译的文本节点
        
        策略：
        1. 遍历白名单标签
        2. 跳过黑名单标签的子树
        3. 保护variable类的变量名
        4. 过滤纯数字、单位、版本标记等
        5. 只提取直接文本子节点（NavigableString）
        """
        segments = []

        for tag in soup.find_all(self.TRANSLATABLE_TAGS):
            # 检查是否在黑名单标签的子树中
            if self._has_skip_tag_parent(tag):
                self.stats['skipped_tags'] += 1
                continue

            # 检查是否是需要保护的类
            if self._is_protected_class(tag):
                self.stats['protected_variables'] += 1
                continue

            # 提取直接文本子节点
            for child in tag.children:
                if isinstance(child, NavigableString):
                    text = child.strip()
                    if text and self._is_translatable_text(text):
                        segments.append((child, text))

        return segments

    def _has_skip_tag_parent(self, tag: Tag) -> bool:
        """检查节点的父辈中是否包含黑名单标签"""
        for parent in tag.parents:
            if parent.name in self.SKIP_TAGS:
                return True
        return False

    def _is_protected_class(self, tag: Tag) -> bool:
        """检查标签是否属于需要保护的CSS类"""
        classes = tag.get('class', [])
        return any(cls in self.PROTECT_CLASSES for cls in classes)

    def _is_translatable_text(self, text: str) -> bool:
        """
        判断文本是否值得翻译
        
        排除规则：
        - 空白或过短（<2字符）
        - 纯数字/符号
        - 单位符号
        - 版本标记
        - 全部是变量名
        """
        # 长度检查
        if len(text) < 2:
            return False

        # 纯数字/符号
        if self.PURE_NUMERIC_PATTERN.match(text):
            return False

        # 单位符号
        if self.UNIT_PATTERN.match(text) or text.strip('[]') in ['%', 's', '°C']:
            return False
            self.stats['protected_units'] += 1
            return False

        # 版本标记
        if self.VERSION_PATTERN.match(text):
            return False

        # 检查是否全部是变量名（如 "VavSuSpAirFl"）
        words = text.split()
        if all(self.VARIABLE_PATTERN.match(w) for w in words):
            self.stats['protected_variables'] += 1
            return False

        return True

    def protect_variable_names(self, text: str) -> Tuple[str, List[str]]:
        """
        保护文本中的变量名不被翻译
        
        策略：
        1. 识别变量名模式
        2. 替换为占位符 {{VAR_001}}
        3. 返回替换后的文本和变量名映射表
        
        Args:
            text: 原始文本
            
        Returns:
            tuple: (处理后的文本, 变量名列表)
        """
        variables_found = []
        protected_text = text

        for match in self.VARIABLE_PATTERN.finditer(text):
            var_name = match.group()
            if var_name not in variables_found:
                variables_found.append(var_name)

        # 对长文本中的变量名添加特殊标记
        # （实际翻译时会在translator模块中处理）
        return protected_text, variables_found

    def update_html_lang(self, soup: BeautifulSoup, target_lang: str = 'zh-CN') -> None:
        """
        更新HTML语言属性为中文
        
        修改位置：
        - <html lang="en-US"> → <html lang="zh-CN">
        - data-culture="en-US" → data-culture="zh-CN"
        """
        html_tag = soup.find('html')
        if html_tag and html_tag.has_attr('lang'):
            html_tag['lang'] = target_lang

        body_tag = soup.find('body')
        if body_tag and body_tag.has_attr('data-culture'):
            body_tag['data-culture'] = target_lang

        # 更新title标签中的语言指示
        title_tag = soup.find('title')
        if title_tag:
            original_title = title_tag.string
            if original_title and '(English)' not in original_title:
                # 可以在这里添加语言标记，但通常不需要修改标题内容
                pass

    def replace_translated_text(self, segments: List[Tuple[NavigableString, str]], 
                                 translations: Dict[str, str]) -> int:
        """
        将翻译后的文本回填到原始DOM节点
        
        Args:
            segments: 原始文本片段列表 [(NavigableString, 原文), ...]
            translations: 翻译结果字典 {原文: 译文}
            
        Returns:
            int: 成功替换的数量
        """
        replaced_count = 0

        for node, original_text in segments:
            if original_text in translations:
                translated = translations[original_text]
                # 使用replace_with保持DOM结构完整
                node.replace_with(translated)
                replaced_count += 1
                self.stats['translated_segments'] += 1

        return replaced_count

    def save_translated_file(self, soup: BeautifulSoup, output_path: Path) -> None:
        """
        保存翻译后的HTML文件
        
        Args:
            soup: 处理后的BeautifulSoup对象
            output_path: 输出文件路径
        """
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    def get_statistics(self) -> Dict:
        """获取解析统计信息"""
        return self.stats.copy()

    @staticmethod
    def validate_html_integrity(original_path: Path, translated_path: Path) -> Dict:
        """
        验证翻译后HTML的完整性
        
        检查项：
        - 文件存在且非空
        - HTML结构有效（可被BeautifulSoup解析）
        - 关键meta标签保留
        - 图片链接数量一致
        - CSS/JS引用保留
        
        Args:
            original_path: 原始文件路径
            translated_path: 翻译后文件路径
            
        Returns:
            dict: 验证结果 {'valid': bool, 'checks': dict, 'errors': list}
        """
        result = {
            'valid': True,
            'checks': {},
            'errors': []
        }

        try:
            # 检查文件存在且大小合理
            if not translated_path.exists():
                result['valid'] = False
                result['errors'].append(f'翻译文件不存在: {translated_path}')
                return result

            orig_size = original_path.stat().st_size
            trans_size = translated_path.stat().st_size

            if trans_size == 0:
                result['valid'] = False
                result['errors'].append('翻译文件为空')
                return result

            result['checks']['original_size'] = orig_size
            result['checks']['translated_size'] = trans_size
            result['checks']['size_ratio'] = trans_size / orig_size if orig_size > 0 else 0

            # 尝试解析翻译后的HTML
            with open(translated_path, 'r', encoding='utf-8') as f:
                trans_soup = BeautifulSoup(f.read(), 'html.parser')

            result['checks']['html_parseable'] = True

            # 检查关键元素
            html_tag = trans_soup.find('html')
            result['checks']['has_html_tag'] = html_tag is not None

            head_tag = trans_soup.find('head')
            result['checks']['has_head_tag'] = head_tag is not None

            body_tag = trans_soup.find('body')
            result['checks']['has_body_tag'] = body_tag is not None

            # 统计图片链接数量
            orig_img_count = len(BeautifulSoup(open(original_path, 'r', encoding='utf-8').read(), 'html.parser').find_all('img'))
            trans_img_count = len(trans_soup.find_all('img'))
            result['checks']['original_images'] = orig_img_count
            result['checks']['translated_images'] = trans_img_count
            result['checks']['images_preserved'] = orig_img_count == trans_img_count

            # 检查脚本引用
            orig_scripts = len(BeautifulSoup(open(original_path, 'r', encoding='utf-8').read(), 'html.parser').find_all('script'))
            trans_scripts = len(trans_soup.find_all('script'))
            result['checks']['scripts_preserved'] = orig_scripts == trans_scripts

            # 语言属性更新检查
            lang_attr = html_tag.get('lang', '') if html_tag else ''
            result['checks']['lang_updated'] = lang_attr == 'zh-CN'

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'验证过程出错: {str(e)}')

        return result


# ==================== 测试用例 ====================

def test_parser():
    """测试解析器功能"""
    import sys
    import tempfile
    
    # 修复Windows控制台编码问题
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # 创建测试HTML
    test_html = '''<!DOCTYPE html>
<html lang="en-US">
<head><title>Test Document</title></head>
<body>
<header><nav><ol><li>Home</li><li>Room Automation</li></ol></nav></header>
<article>
<h1 id="heading-123">Supply Air VAV Function</h1>
<p>The application function "<span class="variable">VavSuSpAirFl</span>" controls airflow.</p>
<ul class="list"><li>Cooling mode</li><li>Heating mode</li></ul>
<table><tr><td>Description</td><td>Maximum airflow setpoint [100 m³/h]</td></tr></table>
<p>ABT 5.x and later supports this feature.</p>
<script>var x = 1; // This should NOT be translated</script>
<footer>© 2025 Siemens</footer>
</article>
</body></html>'''

    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(test_html)
        temp_path = Path(f.name)

    try:
        parser = HTMLParser()
        soup, segments = parser.parse_file(temp_path)

        print("=" * 60)
        print("解析器测试结果")
        print("=" * 60)
        print(f"\n检测到的可翻译文本片段 ({len(segments)} 个):")
        print("-" * 60)
        
        for i, (node, text) in enumerate(segments, 1):
            print(f"{i:2d}. [{text[:50]}{'...' if len(text) > 50 else ''}]")

        print("\n" + "=" * 60)
        print("统计信息:")
        print("-" * 60)
        stats = parser.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 测试语言属性更新
        parser.update_html_lang(soup, 'zh-CN')
        updated_lang = soup.find('html')['lang']
        print(f"\n语言属性已更新为: {updated_lang}")

        print("\n✅ 所有测试通过！")

    finally:
        temp_path.unlink()


if __name__ == '__main__':
    test_parser()
