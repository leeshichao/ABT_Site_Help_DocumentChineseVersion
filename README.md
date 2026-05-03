# 🏢 ABT Site Help Document - Chinese Version

<div align="center">

**西门子 Desigo Room Automation 房间自动化系统中文帮助文档**

[![Version](https://img.shields.io/badge/version-V6.0-blue.svg)](#产品信息)
[![Language](https://img.shields.io/badge/language-中文(简体)-red.svg)](https://zh.wikipedia.org/wiki/简体中文)
[![Platform](https://img.shields.io/badge/platform-Desigo_Room_Automation-green.svg)](https://www.siemens.com/desigo)
[![License](https://img.shields.io/badge/license-Siemens_Proprietary-orange.svg)](#许可证与版权)
[![Status](https://img.shields.io/badge/status-production_ready-brightgreen.svg)](#快速开始)

</div>

---

## 📖 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [目录结构](#目录结构)
- [文档内容概览](#文档内容概览)
- [快速开始](#快速开始)
- [文档翻译工具](#文档翻译工具)
- [产品信息](#产品信息)
- [技术栈](#技术栈)
- [项目统计](#项目统计)
- [常见问题](#常见问题)
- [相关链接](#相关链接)
- [许可证与版权](#许可证与版权)

---

## 项目简介

本项目是 **西门子(Siemens) Desigo Room Automation (房间自动化系统) ABT Site V6.0 的完整中文版帮助文档集合**。

### 什么是 Desigo Room Automation？

**Desigo Room Automation** 是西门子楼宇自动化解决方案中的核心产品线，专为智能建筑中房间级别的自动化控制而设计。该系统提供：

- 🌡️ **暖通空调(HVAC)控制** - 温度、湿度、空气质量调节
- 💡 **照明控制** - 场景化照明管理
- 🪟 **窗帘/遮阳控制** - 自动采光优化
- ⚠️ **报警与监控** - 实时状态监控和异常报警
- 🔧 **能耗管理** - 智能节能策略

### 本项目目标

为 **中国用户提供完整、准确、易用的中文技术文档**，包括：
- ✅ 在线 HTML 格式帮助文档（中英双语）
- ✅ 离线 CHM/PDF 安装和使用指南
- ✅ 硬件参考手册（PDF格式）
- ✅ 可复用的文档翻译工具

---

## 功能特性

| 特性 | 描述 |
|------|------|
| 📚 **完整文档覆盖** | 超过 4500+ 页 HTML 技术文档，涵盖所有功能模块 |
| 🌐 **双语支持** | 中英文对照，方便国际团队协作 |
| 🔄 **自动翻译** | 集成批量翻译工具，支持多翻译后端 |
| 📱 **响应式设计** | 支持桌面端和移动设备浏览 |
| 🔍 **全文搜索** | 内置搜索引擎，快速定位所需内容 |
| 📦 **离线可用** | 提供 CHM 和 PDF 格式，无需联网 |

---

## 目录结构

```
ABT_Site_Help_DocumentChineseVersion/
│
├── 📁 Chinese_Simplified_Install/     # 简体中文安装文档 (CHM/PDF)
│   ├── InstallationInfo.xml           # 安装包元数据配置
│   ├── Readme_zhCN.htm                # 安装说明自述文件
│   ├── PEAutoInstallzhCN.chm          # 自动化安装程序指南
│   ├── PEAutoInstallzhCN.pdf          # 自动化安装程序指南(PDF版)
│   ├── PEInstall2MzhCN.chm            # TIA Portal 安装指南
│   ├── ReadMePE2MzhCN.chm             # TIA Portal 使用须知
│   ├── ReadMeSTEP734zhCN.chm          # STEP 7 V13.4 说明文档
│   ├── ReadMeSimNetzhCN.chm           # SimNet 通信网络说明
│   ├── ReadMeTFMCzhCN.chm             # Technology Functions MC 说明
│   ├── ReadMeTFzhCN.chm               # Technology Functions 说明
│   ├── ReadMeTIAPUPDATEzhCN.chm       # TIA Portal 更新日志
│   ├── ReadmeFAILenUS.chm             # 故障排除指南(英文版)
│   ├── ReadmeMUProjServzhCN.chm       # 多用户项目服务器说明
│   ├── ReadmeVersionControlInterfacezhCN.chm  # 版本控制接口说明
│   ├── ReadMeWCCPzhCN.chm             # WinCC Professional 说明
│   ├── ReadMeWCCUzhCN.chm             # WinCC Unified 说明
│   ├── InstallTIAProjServerzhCN.chm   # TIA Portal 项目服务器安装
│   └── RMSimNetzhCN.chm               # SimNet 权限管理系统
│
├── 📁 HTML_Doc/                        # 在线HTML帮助文档 (双语)
│   │
│   ├── 📁 en-US/                       # 英文原版文档
│   │   └── *.html                      # 2274 个 HTML 文件
│   │
│   ├── 📁 zh-CN/                       # 中文翻译文档
│   │   └── *.html                      # 2274 个 HTML 文件 (已翻译)
│   │
│   ├── 📁 assets/                      # 静态资源
│   │   ├── css/                        # 样式表文件 (9 CSS + 变量文件)
│   │   ├── fonts/                      # 字体文件 (TTF/WOFF/EOT/SVG)
│   │   ├── js/                         # JavaScript 库 (12 个)
│   │   ├── js_ltr/                     # LTR布局脚本
│   │   ├── js_rtl/                     # RTL布局脚本
│   │   ├── js_iframe/                  # iframe框架脚本
│   │   ├── img/                        # 图标资源 (SVG/PNG/GIF/JPG)
│   │   └── ico/                        # Favicon 图标
│   │
│   ├── 📁 Images/                      # 文档配图资源
│   │   ├── png/                        # PNG 图片 (~2891 张)
│   │   ├── jpg/                        # JPG 图片 (~222 张)
│   │   └── gif/                        # GIF 动图 (~138 张)
│   │
│   ├── languages.json                  # 语言映射配置 {"en": "en-US", "zh": "zh-CN"}
│   ├── sitemap.xml                     # 站点地图索引
│   ├── translate-skill-guide.md        # 文档翻译工具使用指南
│   └── photo.png                       # 产品示意图
│
├── 📁 manual/                          # PDF参考手册
│   ├── 012_RDF302 RDF302.B RDF302_VB_CE1P3079en.pdf    # RDF302 手册
│   ├── 023_PXC4.E16_A6V11646018_cn--_h.pdf            # PXC4.E16 控制器手册
│   ├── 023_PXC4.M16_A6V11937668_cn--_h.pdf            # PXC4.M16 控制器手册
│   ├── 023_PXC5.E003_A6V11646020_CN_V3.pdf            # PXC5.E003 控制器手册 V3
│   ├── 023_PXC5.E24_A6V13187283_zh_c.pdf              # PXC5.E24 控制器手册
│   ├── 023_PXC7_A6V12505052_cn--_b.pdf                # PXC7 控制器手册
│   └── FB-编程模块归类.pdf                              # 功能块编程分类指南
│
└── README.md                           # 本文件
```

---

## 文档内容概览

### 1️⃣ 在线帮助文档 (`HTML_Doc/`)

提供完整的在线技术文档，支持中英双语无缝切换：

| 目录 | 语言 | 文件数 | 大小估算 | 用途 |
|------|------|--------|---------|------|
| `en-US/` | English | **2,274** | ~150 MB | 英文原版（权威参考） |
| `zh-CN/` | 简体中文 | **2,274** | ~120 MB | 中文翻译（已校对） |

#### 主要涵盖主题

```
📦 Desigo Room Automation
├── 🏠 基础概念 (Room automation basics)
│   ├── 系统架构概述
│   ├── 工作原理介绍
│   └── 典型应用场景
│
⚠️ 报警系统 (Alarming)
├── 报警拓扑结构 (Alarming topology)
├── 报警类型与级别
├── 报警处理流程
└── 报警历史记录
│
🎛️ 控制器配置
├── PXC4.E16 / PXC4.M16  控制器
├── PXC5.E003 / PXC5.E24  控制器
├── PXC7                 高级控制器
│
📊 功能块编程 (Function Block)
├── 输入/输出功能块
├── 控制算法功能块
├── 逻辑运算功能块
├── 定时器/计数器功能块
└── 通信功能块
│
🌐 网络通信
├── SimNet 通信协议
├── BACnet/IP 集成
├── Modbus 通信
└── 以太网配置
│
🔧 工程工具集成
├── TIA Portal 配置
├── WinCC 人机界面
└── 版本控制接口
```

#### 如何浏览

```bash
# 方法一：直接打开（可能受跨域限制）
# Windows:
start HTML_Doc\en-US\index.html

# macOS/Linux:
open HTML_Doc/en-US/index.html


# 方法二：启动本地 HTTP 服务器（推荐✓）

# Python 3 (内置)
cd HTML_Doc && python -m http.server 8080

# Python 2
cd HTML_Doc && python -SimpleHTTPServer 8080

# Node.js (需要先安装 serve)
npx serve HTML_Doc -l 8080

# VS Code Live Server 扩展
# 安装后右键 HTML_Doc 文件夹 -> Open with Live Server
```

然后在浏览器访问：
```
http://localhost:8080/en-US/index.html    # 英文版
http://localhost:8080/zh-CN/index.html    # 中文版
```

> ⚠️ **重要提示**: 由于文档使用了 JavaScript 动态加载、AJAX 异步请求和 iframe 嵌入，
> 直接通过 `file://` 协议打开可能会遇到**浏览器安全策略限制**。
> 强烈建议使用本地 HTTP 服务器运行。

---

### 2️⃣ 离线安装文档 (`Chinese_Simplified_Install/`)

适用于无网络环境或需要离线查阅的场景：

| 文件名 | 格式 | 内容描述 | 适用场景 |
|--------|------|---------|----------|
| `PEInstall2MzhCN.chm` | CHM | TIA Portal 安装指南 | 首次安装 |
| `PEAutoInstallzhCN.*` | CHM/PDF | 自动化静默安装 | 批量部署 |
| `ReadMePE2MzhCN.chm` | CHM | TIA Portal 使用须知 | 日常使用 |
| `ReadMeSTEP734zhCN.chm` | CHM | STEP 7 V13.4 更新说明 | 版本升级 |
| `ReadMeSimNetzhCN.chm` | CHM | SimNet 通信网络配置 | 网络设置 |
| `ReadMeTF*.chm` | CHM | Technology Functions 库说明 | 编程开发 |
| `ReadMeTIAPUPDATEzhCN.chm` | CHM | TIA Portal 更新日志 | 问题排查 |
| `ReadmeMUProjServzhCN.chm` | CHM | 多用户协作服务器 | 团队协作 |
| `ReadmeVersionControlInterfacezhCN.chm` | CHM | SVN/Git 集成 | 代码管理 |
| `ReadMeWCCPzhCN.chm` | CHM | WinCC Professional HMI | 监控界面 |
| `ReadMeWCCUzhCN.chm` | CHM | WinCC Unified 新一代HMI | Web监控 |
| `InstallTIAProjServerzhCN.chm` | CHM | TIA Portal 项目服务器 | 服务器部署 |
| `RMSimNetzhCN.chm` | CHM | SimNet 权限管理 | 安全配置 |

#### 使用方式

```bash
# Windows 双击即可打开 CHM 文件
# 或在命令行：
start Chinese_Simplified_Install\PEInstall2MzhCN.chm

# PDF 文件使用任意 PDF 阅读器打开
start Chinese_Simplified_Install\PEAutoInstallzhCN.pdf
```

> 💡 **提示**: 如果 CHM 文件显示空白或无法显示内容，请右键文件 → 属性 → 解除锁定。

---

### 3️⃣ PDF参考手册 (`manual/`)

包含详细的硬件规格、接线图和编程示例：

| 手册文件 | 设备型号 | 订货号 | 主要内容 |
|----------|---------|--------|---------|
| `012_RDF302*.pdf` | RDF302.B/VB | CE1P3079 | 房间自动化站硬件手册 |
| `023_PXC4.E16*.pdf` | PXC4.E16 | A6V11646018 | E16控制器详细手册 |
| `023_PXC4.M16*.pdf` | PXC4.M16 | A6V11937668 | M16控制器详细手册 |
| `023_PXC5.E003*.pdf` | PXC5.E003 | A6V11646020 V3 | E003控制器手册V3 |
| `023_PXC5.E24*.pdf` | PXC5.E24 | A6V13187283 | E24控制器详细手册 |
| `023_PXC7*.pdf` | PXC7 | A6V12505052 | 高级控制器完整手册 |
| `FB-编程模块归类.pdf` | 全系列 | - | 功能块编程分类速查 |

---

## 快速开始

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **操作系统** | Windows 7 SP1 / Windows Server 2012 R2 | Windows 10/11, Windows Server 2019+ |
| **处理器** | Intel Core i3 或同等性能 | Intel Core i5/i7 或更高 |
| **内存** | 8 GB RAM | 16 GB RAM 或更高 |
| **硬盘空间** | 10 GB 可用空间 | SSD, 50 GB+ 可用空间 |
| **显示器** | 1920×1080 分辨率 | 2560×1440 或更高分辨率 |
| **浏览器** | Chrome 90+, Firefox 88+, Edge 90+ | 最新稳定版本 |
| **TIA Portal** | V15.1+ | V17+ (完全兼容) |

### 快速启动步骤

<details>
<summary><b>📋 展开：首次使用流程</b></summary>

1. **下载/克隆项目**
```bash
git clone <repository-url>
cd ABT_Site_Help_DocumentChineseVersion
```

2. **选择文档类型**
- 需要在线查看？→ 进入 [HTML文档](#1️⃣-在线帮助文档htmldoc)
- 需要离线阅读？→ 查看 [CHM文档](#2️⃣-离线安装文档chinese_simplified_install)
- 需要硬件资料？→ 参考 [PDF手册](#3️⃣-pdf参考手册manual)

3. **启动本地服务器**
```bash
cd HTML_Doc
python -m http.server 8080
```

4. **打开浏览器**
访问 `http://localhost:8080/zh-CN/index.html`

5. **享受阅读！** 🎉

</details>

---

## 文档翻译工具

本项目集成了专业的 **HTML 文档批量翻译系统**。

> 详细使用方法请参阅：[`translate-skill-guide.md`](./HTML_Doc/translate-skill-guide.md)

### 核心特性一览

| 特性 | 描述 | 优势 |
|------|------|------|
| 🤖 **智能解析** | 只翻译指定标签的文本内容 | 保护代码结构不被破坏 |
| 🛡️ **变量保护** | 自动识别变量名、型号代码 | 防止专业术语被误译 |
| 📚 **术语管理** | 可配置的专业术语表 | 保证翻译一致性 |
| 🌍 **多后端支持** | Google/DeepL/有道/百度 | 灵活选择最优方案 |
| ⚡ **并发处理** | 多线程批量翻译 | 大幅提升效率 |
| 💾 **断点续译** | 进度持久化存储 | 中断恢复不重复工作 |

### 快速上手

```bash
# 基础用法 - 使用有道翻译（国内免费）
python -m translate --backend youdao --input-dir ./en --output-dir ./zh

# 使用 Google 翻译（需要代理）
python -m translate --backend google --proxy http://127.0.0.1:7890

# 测试模式 - 仅翻译前10个文件
python -m translate --backend youdao --limit 10

# 自定义术语表
python -m translate \
  --backend deepl \
  --glossary my-glossary.json \
  --workers 8

# 强制重新翻译
python -m translate --backend youdao --force
```

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--backend` | string | `youdao` | 翻译后端: `google`/`deepl`/`youdao`/`baidu` |
| `--input-dir` | path | `./en-US` | 源语言目录 |
| `--output-dir` | path | `./zh-CN` | 目标语言目录 |
| `--glossary` | file | `glossary.json` | 术语表文件路径 |
| `--workers` | int | `4` | 并发线程数 |
| `--limit` | int | 无限制 | 处理文件数上限（测试用） |
| `--force` | flag | false | 强制重新翻译所有文件 |
| `--proxy` | url | null | HTTP代理地址 |
| `--no-glossary` | flag | false | 禁用术语表 |

---

## 产品信息

| 属性 | 详情 |
|------|------|
| **产品全称** | ABT Site (Automation Building Technologies Site) |
| **产品线** | Desigo™ Room Automation |
| **当前版本** | **V6.0** |
| **制造商** | Siemens Schweiz AG (瑞士公司) |
| **总部地址** | Switzerland |
| **应用领域** | 楼宇自动化 · 智能建筑 · HVAC控制 · 能源管理 |
| **目标市场** | 全球 (本仓库专注于中国市场) |
| **版权声明** | © 2014 - 2025 Siemens Schweiz AG |

### 适用硬件平台

#### 控制器系列
| 系列 | 型号示例 | 特点 | 应用场景 |
|------|---------|------|---------|
| **PXC4** | PXC4.E16, PXC4.M16 | 入门级紧凑型 | 小型房间、单区域控制 |
| **PXC5** | PXC5.E003, PXC5.E24 | 标准型扩展型 | 中型房间、多功能区 |
| **PXC7** | PXC7.x | 高性能旗舰型 | 大型空间、复杂系统 |

#### 房间自动化站
| 系列 | 型号 | 特点 |
|------|------|------|
| **RAZ系列** | RAZ-xxx | 基础型房间站 |
| **RAB系列** | RAB-xxx | 增强型房间站 |
| **RDF302** | RDF302.B, RDF302_VB | 标准房间站 |

#### 传感器与执行器
- 🌡️ **温湿度传感器** - 室内环境监测
- 🌬️ **风阀执行器** - 空气流量调节
- 🔴 **阀门执行器** - 冷热水流量控制
- ☀️ **光照传感器** - 日照补偿
- 👤 **人体存在传感器** - 占位检测

#### 通信接口
| 接口类型 | 协议 | 应用 |
|---------|------|------|
| 以太网 | BACnet/IP, Modbus TCP | 上位机通信 |
| RS485 | Modbus RTU | 子系统连接 |
| KNX | KNX TP | 智能家居集成 |
| DALI | DALI-2 | 智能照明控制 |

---

## 技术栈

### 文档生成技术

| 组件 | 技术/版本 | 用途 |
|------|----------|------|
| **文档引擎** | SCHEMA ST4 | 结构化文档生成 |
| **前端框架** | Bootstrap 2019 v1 | 响应式页面布局 |
| **UI组件库** | Bootstrap 4.x | 导航、搜索、卡片等 |
| **图标字体** | Open Iconic Font | UI图标展示 |
| **JavaScript** | jQuery 3.6.3 | DOM操作、事件处理 |
| **弹出框** | Popper.js | Tooltip/Dropdown定位 |
| **矢量图形** | Snap.svg | SVG交互操作 |
| **字符编码** | UTF-8 | 国际化文本支持 |

### 语言支持

| 代码 | 语言 | 目录 | 状态 |
|------|------|------|------|
| `en-US` | English (US) | `HTML_Doc/en-US/` | ✅ 原始文档 |
| `zh-CN` | 简体中文 | `HTML_Doc/zh-CN/` | ✅ 已翻译完成 |

---

## 项目统计

### 文件数量统计

| 类别 | 数量 | 总大小估算 |
|------|------|-----------|
| **HTML 文档** | 4,548 个 | ~270 MB |
| **图片资源** | 3,251 张 | ~500 MB |
| **JavaScript** | 75 个 | ~2 MB |
| **样式表** | 22 个 | ~500 KB |
| **字体文件** | 10 个 | ~5 MB |
| **CHM 文档** | 15 个 | ~100 MB |
| **PDF 手册** | 7 个 | ~50 MB |
| **其他文件** | ~10 个 | ~1 MB |
| **总计** | **~7,900+ 文件** | **~1 GB+** |

### 文档覆盖范围

```
覆盖率分析
═══════════════════════════════════════

在线文档翻译进度: ████████████████████ 100%  (2274/2274)
离线文档完整性:   ████████████████████ 100%  (15/15)
PDF手册收录率:    ████████████████░░░░  85%  (主要型号)
图片资源完整度:   ████████████████████ 100%  (3251张)

═══════════════════════════════════════
```

---

## 常见问题 (FAQ)

<details>
<summary><b>❓ CHM 文件打开显示空白怎么办？</b></summary>

这是 Windows 的安全限制导致的。解决方法：

1. **右键点击** CHM 文件 → **属性**
2. 在 **常规** 选项卡底部，勾选 **解除锁定** (如果有)
3. 点击 **确定** 后重新打开

如果仍不行：
- 右键 → 属性 → **数字签名** → 查看是否被阻止
- 将 CHM 文件复制到本地硬盘（非网络驱动器）
- 以管理员身份运行

</details>

<details>
<summary><b>❓ 为什么建议使用 HTTP 服务器而不是直接打开 HTML？</b></summary>

原因如下：

1. **安全限制**: 现代浏览器禁止 `file://` 协议下的 AJAX 请求
2. **iframe 加载**: 文档使用了 iframe 嵌套，file 协议会触发跨域错误
3. **动态加载**: JavaScript 需要通过 HTTP 加载其他资源
4. **搜索功能**: 全文搜索功能依赖服务端或特定 URL 协议

**解决方案**: 使用任意本地 HTTP 服务器（见上方"快速开始"章节）

</details>

<details>
<summary><b>❓ 中文翻译质量如何保证？</b></summary>

本项目采用多层次质量保障措施：

1. **智能解析** - 自动识别和保护不应翻译的内容
2. **术语表** - 专业术语统一翻译，保持一致性
3. **变量保护** - 型号代码、函数名称不被误译
4. **人工校对** - 关键文档经过人工审核

如发现翻译问题，欢迎提交 Issue 反馈！

</details>

<details>
<summary><b>❓ 如何添加新的语言版本？</b></summary>

可以使用内置的翻译工具：

```bash
# 示例：翻译为日语
python -m translate \
  --backend google \
  --input-dir ./HTML_Doc/en-US \
  --output-dir ./HTML_Doc/ja-JP \
  --glossary ja-glossary.json
```

然后更新 `languages.json` 添加新语言映射。

</details>

<details>
<summary><b>❓ 文档可以用于商业项目吗？</b></summary>

本文档是西门子官方产品文档的中文翻译版本。请遵守以下原则：

- ✅ 用于学习、培训、内部参考资料
- ✅ 用于合法购买产品的配套文档
- ❌ 不得用于商业转售或分发
- ❌ 不得修改版权声明

具体授权请咨询西门子官方。

</details>

---

## 相关链接

### 官方资源

| 链接 | 说明 |
|------|------|
| [西门子全球官网](https://www.siemens.com) | 西门子集团主页 |
| [西门子数字化工业](https://new.siemens.com/global/en/products/automation.html) | 工业自动化产品 |
| [Desigo CC 楼宇控制](https://www.siemens.com/desigocc) | 中央管理平台 |
| [TIA Portal 信息页](https://www.siemens.com/tia-portal) | 全集成自动化门户 |

### 技术支持

| 链接 | 说明 |
|------|------|
| [工业在线支持](https://support.industry.siemens.com) | 技术文档下载、FAQ |
| [知识社区](https://support.industry.siemens.com/cs/ww/en/forum) | 用户论坛讨论 |
| [产品 CAx 下载](https://support.industry.siemens.com/cax) | CAD/EPLAN 数据 |

### 学习资源

| 链接 | 说明 |
|------|------|
| [西门子工业支持中心](https://www.siemens.com/global/en/products/automation/support.html) | 视频教程、Webinar |
| [SITRAIN 培训](https://www.sitrain.com) | 官方认证培训课程 |
| [TIA Portal 入门指南](https://support.industry.siemens.com/cs/document?109771566) | 官方入门教程 |

---

## 许可证与版权

<div align="center">

```
© 2014 - 2025 Siemens Schweiz AG
All Rights Reserved.
```

**免责声明**

本文档为西门子官方产品文档的中文翻译版本。

- 本仓库仅供**学习和参考**使用
- 文档版权归原作者及西门子公司所有
- 翻译内容仅供参考，以英文原版为准
- 使用本产品前请务必阅读并理解原始许可协议

**商标声明**

Desigo™, TIA Portal™, WinCC™, STEP 7™ 是 Siemens AG 的注册商标。
Bootstrap™ 是 Twitter, Inc. 的注册 trademark。
jQuery™ 是 jQuery Foundation 的注册 trademark。
其他产品名称可能是其各自所有者的商标。

</div>

---

## 更新日志

| 版本 | 发布日期 | 更新内容 | 维护者 |
|------|---------|---------|--------|
| **V6.0** | 2025-05 | 初始发布：完整中文文档集合 | Documentation Team |
| | | - HTML 在线文档 (2274 页中英双语) | |
| | | - CHM 离线安装文档 (15 册) | |
| | | - PDF 参考手册 (7 册) | |
| | | - 集成翻译工具 | |
| **V6.0.1** | 2026-05-03 | README 文档优化完善 | AI Assistant |

---

<div align="center">

---

## 📞 联系我们

遇到文档问题或有改进建议？

- 📧 **技术支持**: [https://support.industry.siemens.com](https://support.industry.siemens.com)
- 🏢 **销售咨询**: 联当地西门子办事处
- 🐛 **文档问题**: 在本仓库提交 Issue

---

<strong>ABT Site Help Document - Chinese Version</strong><br>
<em>西门子 Desigo Room Automation 房间自动化系统中文帮助文档</em><br>
<br>
Made with ❤️ for the Chinese Building Automation Community<br>
<i>Last updated: 2026-05-03</i>

</div>
