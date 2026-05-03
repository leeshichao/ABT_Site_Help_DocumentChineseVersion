# Siemens Desigo Room Automation 文档翻译系统

## 项目概述

这是一个专业的**英文技术文档批量翻译工具**，专门为 Siemens Desigo Room Automation (ABT Site V6.0) 文档系统设计。

### 核心能力

- **全自动翻译**: 2274个HTML文件一键翻译
- **智能解析**: 自动识别并保护变量名、代码、单位符号
- **专业术语**: 内置237条 HVAC/BACnet/Siemens 领域术语对照表
- **高性能**: 多线程并发处理 + 翻译缓存
- **断点续译**: 中断后可从上次位置继续
- **多后端支持**: 有道/MyMemory/Google/DeepL/百度翻译
- **质量保证**: HTML完整性自动验证

---

## 快速开始

### 1. 环境要求

```bash
# Python 3.8+
python --version

# 安装依赖
cd d:\dve\ABT-test\Doc\zh
pip install beautifulsoup4 deep-translator tqdm requests
```

### 2. 重要提示：运行方式

**必须从项目根目录运行**，不要从 `translate` 子目录运行：

```bash
# 正确方式 ✅
cd d:\dve\ABT-test\Doc\zh
python -m translate --help

# 错误方式 ❌
cd d:\dve\ABT-test\Doc\zh\translate
python main.py
```

### 3. 快速测试

```bash
# 检查环境
python -m translate --check-only

# 查看扫描统计
python -m translate --dry-run --limit 5

# 翻译前5个文件（有道翻译 - 推荐中国大陆）
python -m translate --limit 5 --no-banner

# 翻译前5个文件（MyMemory - 备用）
python -m translate --limit 5 --no-banner --backend mymemory
```

### 4. 完整翻译

```bash
# 有道翻译（推荐中国大陆用户）
python -m translate --workers 4 --no-banner

# MyMemory翻译（免费但较慢）
python -m translate --workers 2 --no-banner --backend mymemory

# Google翻译（需要VPN代理）
python -m translate --workers 4 --no-banner --backend google

# DeepL翻译（需要VPN代理）
python -m translate --workers 4 --no-banner --backend deepl-free
```

---

## 项目结构

```
d:\dve\ABT-test\Doc\zh\
├── translate/                      # 翻译工具包
│   ├── __init__.py                 # 包初始化文件
│   ├── __main__.py                 # 入口文件（python -m translate）
│   ├── main.py                     # 主程序逻辑
│   ├── config.py                   # 配置文件
│   ├── html_parser.py              # 智能HTML解析器
│   ├── translator_engine.py         # 翻译引擎（多后端支持）
│   ├── orchestrator.py             # 批量调度器
│   ├── utils.py                    # 工具函数
│   ├── glossary.csv                 # 专业术语表（237条）
│   ├── test_integration.py         # 集成测试
│   ├── README.md                   # 完整文档
│   └── QUICKSTART.md               # 快速入门
│
├── en-US/                          # 英文原版文档（2274个HTML）
├── zh-CN/                          # 中文翻译输出（自动创建）
├── assets/                         # 静态资源
├── Images/                         # 图片资源（3300+张）
└── languages.json                  # 语言映射（已更新含中文）
```

---

## 命令行参数

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | -i | `./en-US` | 输入目录 |
| `--output` | -o | `./zh-CN` | 输出目录 |
| `--backend` | -b | `youdao` | 翻译后端 |
| `--workers` | -w | `4` | 并发线程数 |
| `--limit` | -l | 无限制 | 处理文件数量上限 |
| `--dry-run` | | False | 仅扫描统计 |
| `--no-resume` | | False | 禁用断点续译 |
| `--check-only` | | False | 仅检查环境 |
| `--no-banner` | | False | 不显示横幅 |
| `--log-level` | | INFO | 日志级别 |

### 可用翻译后端

| 后端 | 说明 | 中国大陆 | 推荐度 |
|------|------|---------|--------|
| `youdao` | **有道翻译**（默认） | ✅ 可用 | ⭐⭐⭐⭐⭐ |
| `mymemory` | MyMemory免费 | ✅ 可用 | ⭐⭐⭐ |
| `google` | Google翻译 | ❌ 需代理 | ⭐⭐⭐⭐ |
| `deepl-free` | DeepL免费 | ❌ 需代理 | ⭐⭐⭐⭐⭐ |
| `deepl` | DeepL付费 | ❌ 需代理 | ⭐⭐⭐⭐⭐ |
| `baidu` | 百度翻译 | ✅ 可用 | ⭐⭐⭐⭐ |

### 使用示例

```bash
# 完整翻译（有道，推荐）
python -m translate --workers 4 --no-banner

# 快速测试3个文件
python -m translate --limit 3 --workers 2

# 使用MyMemory翻译
python -m translate --backend mymemory --workers 2

# 查看所有选项
python -m translate --help
```

---

## 技术特性详解

### 1. 智能HTML解析器

#### 白名单过滤（只翻译这些标签）

```html
✅ <p>, <h1>-<h6>     # 标题和段落
✅ <li>                # 列表项
✅ <td>, <th>         # 表格单元格
✅ <span>             # 内联文本（非variable类）
✅ <a>                # 链接文本
✅ <title>            # 页面标题
```

#### 黑名单过滤（跳过这些内容）

```html
❌ <script>           # JavaScript代码
❌ <style>            # CSS样式
❌ <code>, <pre>      # 代码块
❌ <svg>, <math>      # 图形公式
❌ <noscript>         # 替代内容
```

#### 变量名保护（保持原文）

```html
<!-- 这些不会被翻译 -->
<span class="variable">VavSuSpAirFl</span>
<span class="variable">CetVavSu11</span>

<!-- 单位符号保留 -->
[100 m³/h]  [29.4 ft³/min]  [%]  [s]  [°C]

<!-- 版本标记保留 -->
ABT 5.x and later
ABT 4.x and earlier
```

### 2. 专业术语表

内置 **237条** HVAC/BACnet/Siemens 领域专业术语：

| English | Chinese | 类别 |
|---------|---------|------|
| VAV (Variable Air Volume) | 变风量（VAV） | HVAC核心概念 |
| Supply air VAV box | 送风VAV箱 | 设备名称 |
| AHU (Air Handling Unit) | 空气处理机组（AHU） | 核心设备 |
| BACnet object | BACnet对象 | 协议术语 |
| Interlock | 联锁/互锁 | 控制逻辑 |
| Setpoint | 设定值 | 参数类型 |
| Damper position | 风阀开度 | 物理参数 |
| Device mode | 设备模式 | 状态属性 |
| Smoke control | 排烟控制 | 安全功能 |
| Commissioning | 调试 | 工程阶段 |

### 3. 多后端翻译引擎

#### 中国大陆用户推荐方案

**首选：有道翻译** (`--backend youdao`)
- 国内可访问，完全免费
- 无需注册或API密钥
- 翻译速度快
- 质量稳定

**备用：MyMemory** (`--backend mymemory`)
- 完全免费，无需注册
- 每日1000词免费额度
- 速度较慢

#### 海外用户推荐方案

**首选：DeepL** (`--backend deepl-free`)
- 翻译质量最佳
- 适合技术文档
- 需要VPN代理

**备用：Google** (`--backend google`)
- 速度快
- 需要VPN代理

### 4. 批量调度与容错

- **并发控制**: 4-8线程并行（避免触发API速率限制）
- **断点续译**: JSON进度文件记录每个文件的状态
- **错误重试**: 每个文件最多重试3次
- **进度保存**: 实时保存进度
- **详细日志**: 记录每步操作的详细信息

---

## 性能预估

### 文件规模

- **总文件数**: 2,274 个HTML
- **总大小**: 31.85 MB
- **术语表**: 237 条

### 时间估算

| 场景 | 并发线程 | 预估时间 | 备注 |
|------|---------|---------|------|
| 测试5个文件 | 2线程 | 1-3分钟 | 验证效果 |
| 全量翻译（有道） | 4线程 | 12-18小时 | 推荐夜间运行 |
| 全量翻译（有道） | 8线程 | 6-9小时 | 需要稳定网络 |
| 全量翻译（MyMemory） | 2线程 | 20-30小时 | 速度较慢 |

### 成本估算

| 方案 | 成本 | 说明 |
|------|------|------|
| 有道翻译 | **$0** | 完全免费，推荐 |
| MyMemory | **$0** | 免费但有额度限制 |
| Google翻译 | **$0** | 免费50万字符/月 |
| DeepL Free | **$0** | 有限制 |
| DeepL Pro | $20-50/月 | 高质量需求 |

---

## 质量保证机制

### 自动化检查

- ✅ HTML结构完整性
- ✅ 关键元素保留（html/head/body标签）
- ✅ 图片链接完整性
- ✅ JavaScript引用保留
- ✅ CSS样式保留
- ✅ Meta元数据保留
- ✅ 语言属性更新（lang="zh-CN"）

### 抽样检查建议

翻译完成后，人工抽查以下类型的文件：
- **简单页面** (<10KB): 3-5个
- **表格密集页** (30-50KB): 3-5个
- **复杂综合页** (>50KB): 2-3个
- **特殊格式页**: 2-3个

---

## 常见问题FAQ

### Q1: 运行报错 "No module named 'translate'"？
**A**: 必须从项目根目录运行：
```bash
cd d:\dve\ABT-test\Doc\zh
python -m translate --help
```

### Q2: 翻译请求失败怎么办？
**A**: 
1. 检查网络连接
2. 尝试更换翻译后端（有道→MyMemory→Google）
3. 减少并发线程数：`--workers 2`

### Q3: Google翻译无法使用？
**A**: 国内无法直接访问Google，需要VPN代理。建议使用有道翻译。

### Q4: 如何提高翻译质量？
**A**: 
1. 定期审查并扩充术语表（glossary.csv）
2. 对重要页面使用DeepL重新翻译
3. 人工审校关键页面（约5%抽样）

### Q5: 网络中断了怎么办？
**A**: 无需担心！下次运行时会自动从断点继续，不会重复翻译已完成的文件。

### Q6: 如何验证翻译效果？
**A**: 
1. 查看日志：`logs/translation_*.log`
2. 在浏览器打开zh-CN目录的HTML文件预览
3. 对比en-US原版检查差异

---

## 更新日志

### v1.1.0 (2026-05-02)
- ✅ 添加有道翻译后端（推荐中国大陆用户）
- ✅ 添加MyMemory翻译后端（备用方案）
- ✅ 添加百度翻译后端（需要API密钥）
- ✅ 优化Windows兼容性
- ✅ 简化命令行参数

### v1.0.0 (2026-05-02)
- ✅ 初始版本发布
- ✅ 智能HTML解析器
- ✅ 237条专业术语对照表
- ✅ Google/DeepL多后端支持
- ✅ 批量并发处理
- ✅ 断点续译与进度追踪
- ✅ HTML完整性自动验证

---

## 致谢

- **BeautifulSoup4** - HTML解析
- **requests** - HTTP请求
- **tqdm** - 进度条显示
- **Siemens AG** - Desigo Room Automation产品文档

---

**开始翻译你的技术文档吧！**

```bash
cd d:\dve\ABT-test\Doc\zh
python -m translate --help
```
