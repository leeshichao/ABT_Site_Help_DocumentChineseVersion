#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试脚本 - 使用真实文档验证完整翻译流程
测试项目：
  1. 解析不同复杂度的真实HTML文件
  2. 验证变量名/代码保护机制
  3. 执行实际翻译（Google API）
  4. 验证输出HTML完整性
  5. 检查语言属性更新
"""

import sys
import tempfile
from pathlib import Path

# Windows编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def test_real_file_parsing():
    """测试1: 真实HTML文件解析"""
    print("\n" + "="*70)
    print("📋 测试1: 真实HTML文件解析")
    print("="*70)
    
    from html_parser import HTMLParser
    
    base_dir = Path(__file__).parent.parent
    test_files = [
        ('en-US/10142381835.html', '简单页面 (~4KB)'),
        ('en-US/10445337867.html', '中等页面 (~55KB, 含表格)'),
    ]
    
    parser = HTMLParser()
    
    for file_rel, desc in test_files:
        file_path = base_dir / file_rel
        if not file_path.exists():
            print(f"⚠️ 文件不存在，跳过: {file_rel}")
            continue
        
        print(f"\n📄 测试文件: {file_path.name}")
        print(f"   类型: {desc}")
        
        try:
            soup, segments = parser.parse_file(file_path)
            
            print(f"   ✅ 成功解析")
            print(f"   📊 提取文本片段: {len(segments)} 个")
            
            # 显示前5个片段示例
            print("   📝 前5个文本片段:")
            for i, (node, text) in enumerate(segments[:5], 1):
                preview = text[:60] + '...' if len(text) > 60 else text
                print(f"      {i}. [{preview}]")
            
            stats = parser.get_statistics()
            print(f"   🛡️ 保护变量名: {stats['protected_variables']} 个")
            
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")


def test_translation_engine():
    """测试2: 翻译引擎基本功能"""
    print("\n\n" + "="*70)
    print("🔤 测试2: 翻译引擎基本测试")
    print("="*70)
    
    from translator_engine import create_translator
    
    base_dir = Path(__file__).parent
    
    try:
        translator = create_translator(
            backend_type='google',
            glossary_path=base_dir / 'glossary.csv',
            use_free_api=True
        )
        
        # 测试用例
        test_cases = [
            ("Supply air VAV box", "HVAC术语"),
            ("Device mode includes Off and Control mode", "通用描述"),
            ("Maximum airflow setpoint is 100 m³/h", "含单位的文本"),
            ("ABT 5.x and later", "版本标记"),
        ]
        
        print("\n🔄 测试翻译结果:")
        for text, category in test_cases:
            try:
                result = translator.translate_text(text)
                print(f"\n   📝 [{category}]")
                print(f"      原文: {text}")
                print(f"      译文: {result}")
                print(f"      状态: {'✅' if result != text else '⚠️ (未翻译)'}")
            except Exception as e:
                print(f"\n   ❌ [{category}] 翻译失败: {e}")
        
        stats = translator.get_statistics()
        print(f"\n📊 引擎统计:")
        print(f"   总翻译数: {stats['total_translations']}")
        print(f"   缓存命中: {stats['cache_hits']}")
        print(f"   术语匹配: {stats['glossary_matches']}")
        
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("   请运行: pip install deep-translator")
        return False
    
    return True


def test_full_pipeline():
    """测试3: 完整端到端翻译流程"""
    print("\n\n" + "="*70)
    print("🚀 测试3: 完整翻译流程（单文件）")
    print("="*70)
    
    from html_parser import HTMLParser
    from translator_engine import create_translator
    import tempfile
    
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'en-US' / '10142381835.html'
    
    if not input_file.exists():
        print(f"❌ 测试文件不存在: {input_file}")
        return False
    
    print(f"\n📂 输入文件: {input_file.name} ({input_file.stat().st_size/1024:.1f}KB)")
    
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / 'output_test.html'
        
        try:
            # 步骤1: 解析
            parser = HTMLParser()
            soup, segments = parser.parse_file(input_file)
            print(f"\n步骤1 - HTML解析: ✅ | 提取 {len(segments)} 个片段")
            
            if not segments:
                print("⚠️ 无可翻译文本，跳过翻译测试")
                return True
            
            # 步骤2: 翻译
            translator = create_translator(
                backend_type='google',
                glossary_path=Path(__file__).parent / 'glossary.csv',
                use_free_api=True
            )
            
            translations = translator.translate_segments(segments)
            print(f"步骤2 - 文本翻译: ✅ | 翻译 {len(translations)} 个片段")
            
            # 步骤3: 回填到DOM
            replaced = parser.replace_translated_text(segments, translations)
            print(f"步骤3 - 回填DOM: ✅ | 替换 {replaced} 个节点")
            
            # 步骤4: 更新语言属性
            parser.update_html_lang(soup, 'zh-CN')
            lang_attr = soup.find('html')['lang']
            print(f"步骤4 - 语言更新: ✅ | lang='{lang_attr}'")
            
            # 步骤5: 保存
            parser.save_translated_file(soup, output_path)
            print(f"步骤5 - 保存文件: ✅ | 大小: {output_path.stat().st_size/1024:.1f}KB")
            
            # 步骤6: 验证完整性
            validation = HTMLParser.validate_html_integrity(input_file, output_path)
            
            print(f"\n🔍 验证结果:")
            print(f"   HTML可解析:     {'✅' if validation['checks'].get('html_parseable') else '❌'}")
            print(f"   HTML标签存在:   {'✅' if validation['checks'].get('has_html_tag') else '❌'}")
            print(f"   Body标签存在:   {'✅' if validation['checks'].get('has_body_tag') else '❌'}")
            print(f"   图片数量一致:   {'✅' if validation['checks'].get('images_preserved') else '❌'}")
            print(f"   脚本引用保留:   {'✅' if validation['checks'].get('scripts_preserved') else '❌'}")
            print(f"   语言属性已更新: {'✅' if validation['checks'].get('lang_updated') else '❌'}")
            print(f"   整体验证:       {'✅ 通过' if validation['valid'] else '❌ 失败'}")
            
            if validation['errors']:
                print(f"\n⚠️ 验证警告:")
                for error in validation['errors']:
                    print(f"   - {error}")
            
            # 显示翻译后文件的前几行预览
            print(f"\n📖 输出文件预览 (前20行):")
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:20]
                for i, line in enumerate(lines, 1):
                    print(f"   {i:2d}: {line.rstrip()[:80]}")
            
            return validation['valid']
            
        except Exception as e:
            print(f"\n❌ 流程测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """运行所有集成测试"""
    print("\n" + "🧪"*35)
    print("🎯 Siemens Desigo Room Automation 文档翻译系统")
    print("   集成测试套件 v1.0")
    print("🧪"*35)
    
    results = []
    
    # 测试1: 文件解析
    try:
        test_real_file_parsing()
        results.append(('文件解析', True))
    except Exception as e:
        print(f"\n❌ 测试1异常: {e}")
        results.append(('文件解析', False))
    
    # 测试2: 翻译引擎
    try:
        success = test_translation_engine()
        results.append(('翻译引擎', success))
    except Exception as e:
        print(f"\n❌ 测试2异常: {e}")
        results.append(('翻译引擎', False))
    
    # 测试3: 完整流程
    try:
        success = test_full_pipeline()
        results.append(('完整流程', success))
    except Exception as e:
        print(f"\n❌ 测试3异常: {e}")
        results.append(('完整流程', False))
    
    # 输出最终报告
    print("\n\n" + "="*70)
    print("🏆 最终测试报告")
    print("="*70)
    
    all_passed = True
    for name, passed in results:
        status = '✅ PASS' if passed else '❌ FAIL'
        print(f"   {status}  {name}")
        if not passed:
            all_passed = False
    
    print("-"*70)
    final_status = "🎉 全部通过！" if all_passed else "⚠️ 存在失败的测试项"
    print(f"   结果: {final_status}")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
