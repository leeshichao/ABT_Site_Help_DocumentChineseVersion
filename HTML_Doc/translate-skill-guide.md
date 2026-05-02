# HTML文档批量翻译系统 - 通用Skill说明文档

## 📋 Skill概述

### 用途
这是一个通用的HTML文档批量翻译工具，能够将英文（或其他语言）的HTML文档自动翻译为目标语言，同时智能保护代码、变量名、专有名词等不应翻译的内容。

### 适用场景
- 📚 **技术文档翻译** - API文档、SDK文档、用户手册
- 🌐 **网站本地化** - 多语言网站内容翻译
- 📖 **文档库迁移** - 将现有文档库翻译成新语言
- 🔄 **内容本地化** - 产品文档的多语言版本生成

### 核心能力
1. **智能HTML解析** - 只翻译指定标签内容，保护代码结构
2. **变量名保护** - 自动识别并保护驼峰变量名、代码片段
3. **专业术语管理** - 可配置的术语表确保翻译一致性
4. **多翻译后端** - 支持Google/DeepL/有道/百度等多种翻译API
5. **批量并发处理** - 多线程加速，支持大规模文档翻译
6. **断点续译** - 中断后可恢复，避免重复翻译

---

## 🚀 快速开始

### 基础用法

```bash
# 最简单的使用方式
python -m translate --backend google --input-dir ./en --output-dir ./zh

# 使用有道翻译（国内推荐，免费）
python -m translate --backend youdao --input-dir ./en --output-dir ./zh

# 限制翻译前10个文件（测试用）
python -m translate --backend google --limit 10
```

### 完整参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--backend` | 翻译后端 | `youdao` | `google`/`deepl`/`youdao`/`baidu` |
| `--input-dir` | 输入目录 | `./en-US` | `./docs/en` |
| `--output-dir` | 输出目录 | `./zh-CN` | `./docs/zh` |
| `--glossary` | 术语表文件 | `glossary.json` | `./my-terms.json` |
| `--workers` | 并发线程数 | `4` | `8` |
| `--limit` | 限制处理文件数 | `None` | `100` |
| `--force` | 强制重新翻译 | `False` | `--force` |
| `--proxy` | 代理服务器 | `None` | `http://127.0.0.1:7890` |
| `--no-glossary` | 禁用术语表 | `False` | `--no-glossary` |

---

## 🏗️ 系统架构

### 核心模块

```
translate/
├── main.py                 # 命令行入口
├── translator_engine.py    # 翻译引擎核心
├── html_parser.py          # HTML智能解析器
├── orchestrator.py         # 任务编排器
├── config.py               # 配置管理
└── glossary.json           # 术语表（可选）
```

### 工作流程

```
输入HTML文件
    ↓
[HTML解析器] → 提取可翻译文本（按白名单标签）
    ↓
[变量保护器] → 保护变量名/代码/单位符号
    ↓
[术语表替换] → 预替换专业术语
    ↓
[翻译后端] → 调用API翻译
    ↓
[变量恢复器] → 恢复保护的变量
    ↓
[HTML重构] → 生成翻译后的HTML
    ↓
输出HTML文件
```

---

## ⚙️ 配置指南

### 1. 标签白名单配置

**文件**: `html_parser.py` 或 `config.py`

```python
# 可翻译的HTML标签（白名单）
TRANSLATABLE_TAGS = {
    'p',      # 段落
    'h1',     # 一级标题
    'h2',     # 二级标题（可选）
    'h3',     # 三级标题（可选）
    # 可根据需要添加更多标签
}

# 跳过的标签（黑名单）
SKIP_TAGS = {
    'script',   # JavaScript代码
    'style',    # CSS样式
    'code',     # 代码块
    'pre',      # 预格式化文本
    'svg',      # SVG图形
    'math',     # 数学公式
}
```

### 2. 翻译后端配置

**有道翻译（推荐国内用户）**
```python
# 免费使用，无需API密钥
backend = 'youdao'
```

**Google翻译（需代理）**
```bash
# 使用代理访问
python -m translate --backend google --proxy http://127.0.0.1:7890
```

**DeepL翻译（高质量）**
```python
# 需要API密钥
# 在 config.py 中配置
DEEPL_API_KEY = 'your-api-key-here'
```

### 3. 术语表配置

**创建术语表文件** `glossary.json`:

```json
{
  "glossary": [
    {
      "en": "Application",
      "zh-CN": "应用程序"
    },
    {
      "en": "Room Automation",
      "zh-CN": "房间自动化"
    },
    {
      "en": "BACnet",
      "zh-CN": "BACnet"
    }
  ]
}
```

**术语表使用优先级**:
1. 精确匹配（大小写敏感）
2. 长短语优先（避免短词误匹配）
3. 独立单词匹配（避免部分匹配）

---

## 🛠️ 高级功能

### 1. 变量名保护

系统自动识别并保护以下格式:

| 类型 | 示例 | 处理方式 |
|------|------|---------|
| 驼峰变量 | `VavSupplyAir` | 替换为 `__VAR_000__` |
| 全大写缩写 | `ABT` | 替换为 `__VAR_001__` |
| 单位符号 | `m³/h` | 保留不翻译 |
| URL/邮箱 | `https://...` | 完整保留 |
| 专有名词 | `Siemens` | 可配置保留 |

### 2. 批量翻译策略

```python
# 并发配置
orchestrator = TranslationOrchestrator(
    input_dir='./en',
    output_dir='./zh',
    max_workers=4,        # 并发线程数
    batch_size=10,        # 每批处理文件数
    retry_failed=True     # 失败自动重试
)
```

### 3. 断点续译

系统自动生成进度文件 `translation_progress.json`:

```json
{
  "files": [
    {
      "filename": "index.html",
      "status": "done",
      "translated_at": "2026-05-03 10:30:00"
    },
    {
      "filename": "guide.html",
      "status": "pending"
    }
  ]
}
```

**恢复翻译**:
```bash
# 自动跳过已完成的文件
python -m translate --backend google

# 强制重新翻译所有文件
python -m translate --backend google --force
```

---

## 📦 在其他项目中复用

### 方式一：直接复用代码

1. **复制核心模块**:
   ```bash
   cp -r translate/ your-project/tools/translator/
   ```

2. **调整配置**:
   - 修改 `config.py` 中的默认路径
   - 更新 `glossary.json` 中的专业术语
   - 调整 `TRANSLATABLE_TAGS` 白名单

3. **运行翻译**:
   ```bash
   cd your-project/tools/translator
   python -m translate --input-dir ./docs/en --output-dir ./docs/zh
   ```

### 方式二：作为Python包使用

```python
# 在你的项目中
from translate.translator_engine import TranslatorEngine
from translate.html_parser import HTMLParser

# 创建翻译引擎
engine = TranslatorEngine(backend='youdao')

# 翻译单个HTML文件
with open('input.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

parser = HTMLParser()
segments = parser.parse(html_content)
translations = engine.translate_segments(segments)

# 应用翻译
output = parser.apply_translations(html_content, translations)
with open('output.html', 'w', encoding='utf-8') as f:
    f.write(output)
```

---

## 🎯 实战示例

### 示例1：翻译API文档

**场景**: 将英文API文档翻译成中文

```bash
# 1. 准备术语表（API专有名词）
cat > api-glossary.json << EOF
{
  "glossary": [
    {"en": "Endpoint", "zh-CN": "端点"},
    {"en": "Request", "zh-CN": "请求"},
    {"en": "Response", "zh-CN": "响应"},
    {"en": "Authentication", "zh-CN": "身份验证"}
  ]
}
EOF

# 2. 执行翻译
python -m translate \
  --backend youdao \
  --input-dir ./api-docs/en \
  --output-dir ./api-docs/zh \
  --glossary ./api-glossary.json \
  --workers 8
```

### 示例2：网站内容本地化

**场景**: 将静态网站翻译成多种语言

```bash
# 翻译成西班牙语
python -m translate \
  --backend google \
  --input-dir ./website/en \
  --output-dir ./website/es \
  --proxy http://127.0.0.1:7890

# 翻译成法语
python -m translate \
  --backend google \
  --input-dir ./website/en \
  --output-dir ./website/fr \
  --proxy http://127.0.0.1:7890
```

### 示例3：技术手册翻译

**场景**: 翻译产品技术手册，保护型号代码

```python
# 自定义变量保护规则（在 config.py 中）
CUSTOM_VARIABLE_PATTERNS = [
    r'Model-[A-Z0-9]+',     # 匹配 Model-ABC123
    r'Part#[0-9-]+',        # 匹配 Part#123-456
]

# 执行翻译
python -m translate --backend deepl --workers 4
```

---

## 🔧 故障排除

### 问题1：Google翻译需要代理

**解决方案**:
```bash
# 设置代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 或使用参数
python -m translate --backend google --proxy http://127.0.0.1:7890
```

### 问题2：翻译质量不理想

**改进方法**:
1. **完善术语表** - 添加领域专业术语
2. **调整标签白名单** - 避免翻译代码块
3. **切换翻译后端** - 尝试DeepL（质量更高）

### 问题3：变量名被误翻译

**解决方案**:
在 `config.py` 中添加自定义保护规则:

```python
# 保护特定格式的变量
ADDITIONAL_PROTECT_PATTERNS = [
    r'myVar_[0-9]+',      # 保护 myVar_123
    r'config\.[a-z_]+',   # 保护 config.xxx
]
```

---

## 📊 性能优化

### 并发配置建议

| 文档数量 | 单文件大小 | 推荐workers | 预计耗时 |
|---------|-----------|-------------|---------|
| < 100   | < 100KB   | 4           | 5分钟   |
| 100-1000| 100-500KB | 8           | 30分钟  |
| > 1000  | > 500KB   | 16          | 2小时   |

### 缓存机制

系统自动缓存已翻译内容到 `translation_cache.json`:

```json
{
  "cache": {
    "md5_hash_of_text": {
      "source": "Hello World",
      "target": "你好世界",
      "backend": "google",
      "timestamp": "2026-05-03 10:00:00"
    }
  }
}
```

**清除缓存**:
```bash
rm translation_cache.json
```

---

## 📝 最佳实践

### 1. 翻译前准备

- ✅ **备份原始文件** - 避免翻译错误导致数据丢失
- ✅ **准备术语表** - 确保专业术语翻译一致性
- ✅ **测试小批量** - 使用 `--limit 5` 测试翻译质量
- ✅ **检查标签白名单** - 确保只翻译需要的内容

### 2. 翻译后验证

- ✅ **检查HTML完整性** - 确保标签未损坏
- ✅ **验证变量保护** - 确保代码未被篡改
- ✅ **人工审核** - 关键页面进行人工校对

### 3. 持续维护

- 🔄 **更新术语表** - 根据反馈不断完善
- 🔄 **优化变量规则** - 添加新的保护模式
- 🔄 **升级翻译后端** - 跟踪API更新

---

## 📄 许可证与贡献

### 开源协议
MIT License - 可自由用于个人或商业项目

### 贡献指南
欢迎提交Issue和Pull Request来改进此工具：

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

---

## 📚 参考资料

### 相关文档
- [HTML解析器使用指南](./translate/html_parser.py)
- [翻译引擎API文档](./translate/translator_engine.py)
- [配置参数详细说明](./translate/config.py)

### 外部资源
- [Google Translate API文档](https://cloud.google.com/translate/docs)
- [DeepL API文档](https://www.deepl.com/docs-api)
- [有道智云API文档](https://ai.youdao.com/DOCSIRMA/html/trans/api/wbfy/index.html)

---

## 🎉 总结

这个HTML文档批量翻译系统是一个强大且灵活的工具，通过智能解析、变量保护和术语管理，能够高效地完成技术文档的翻译工作。

**核心优势**:
- ✅ 智能保护代码和变量
- ✅ 支持多种翻译后端
- ✅ 批量并发处理
- ✅ 断点续译机制
- ✅ 高度可配置

**适用项目**:
- 开源项目文档本地化
- 企业技术文档翻译
- 多语言网站内容管理
- API文档国际化

通过本指南，你可以快速将此系统适配到任何需要HTML文档翻译的项目中。
