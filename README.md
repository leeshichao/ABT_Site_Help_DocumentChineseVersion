# ABT Site 帮助文档 (中文版)

[![Version](https://img.shields.io/badge/version-V6.0-blue.svg)](https://www.siemens.com)
[![Language](https://img.shields.io/badge/language-中文(简体)-red.svg)](https://zh.wikipedia.org/wiki/简体中文)
[![Platform](https://img.shields.io/badge/platform-Desigo_Room_Automation-green.svg)](https://www.siemens.com/desigo)

## 项目简介

本项目是 **西门子(Siemens) Desigo Room Automation (房间自动化系统) ABT Site V6.0 的中文版帮助文档集合**。

Desigo Room Automation 是西门子楼宇自动化解决方案中的核心产品，用于智能建筑中房间级别的暖通空调(HVAC)、照明和窗帘等系统的自动化控制。本项目提供了完整的技术文档、安装指南和使用手册，方便中国用户快速上手使用该系统。

---

## 目录结构

```
ABT_Site_Help_DocumentChineseVersion/
├── Chinese_Simplified_Install/    # 简体中文安装文档
│   ├── InstallationInfo.xml       # 安装包信息配置
│   ├── Readme_zhCN.htm            # 安装说明自述文件
│   ├── PEAutoInstallzhCN.*        # 自动化安装指南 (CHM/PDF)
│   ├── PEInstall2MzhCN.chm        # TIA Portal 安装指南
│   └── ReadMe*.chm                # 各模块说明文档
├── HTML_Doc/                      # 在线HTML帮助文档 (双语)
│   ├── en-US/                     # 英文原版 (2274+ 个HTML文件)
│   ├── zh-CN/                     # 中文翻译版 (2274+ 个HTML文件)
│   ├── assets/                    # 静态资源 (CSS/JS/字体/图标)
│   ├── Images/                    # 文档图片资源 (3200+ 张图片)
│   ├── languages.json             # 语言映射配置
│   ├── sitemap.xml                # 站点地图
│   └── translate-skill-guide.md   # 文档翻译工具使用指南
├── manual/                        # PDF参考手册
│   ├── 012_*.pdf                  # RDF302 模块手册
│   ├── 023_*.pdf                  # PXC4/PXC5/PXC7 控制器手册
│   └── FB-编程模块归类.pdf         # 功能块编程指南
└── README.md                      # 本文件
```

---

## 文档内容概览

### 1. 在线帮助文档 (`HTML_Doc/`)

提供完整的在线技术文档，支持中英双语切换：

| 目录 | 语言 | 文件数量 | 说明 |
|------|------|---------|------|
| `en-US/` | English | 2,274 | 英文原版文档 |
| `zh-CN/` | 简体中文 | 2,274 | 中文翻译文档 |

**主要涵盖主题**：
- 🏠 **Desigo Room Automation 基础知识**
- ⚠️ **报警系统 (Alarming)** - 报警拓扑、报警处理
- 🔧 **控制器配置** - PXC4.E16, PXC4.M16, PXC5, PXC7 等
- 📊 **功能块编程** - FB 编程模块归类与使用
- 🔌 **设备集成** - 各类传感器、执行器配置
- 🌐 **网络通信** - SimNet 通信配置

**查看方式**：
```bash
# 直接在浏览器中打开
open HTML_Doc/en-US/index.html    # 英文版
open HTML_Doc/zh-CN/index.html    # 中文版
```

### 2. 离线安装文档 (`Chinese_Simplified_Install/`)

提供 CHM 和 PDF 格式的离线文档：

| 文件名 | 格式 | 内容描述 |
|--------|------|---------|
| `PEInstall2MzhCN.chm` | CHM | TIA Portal 安装指南 |
| `PEAutoInstallzhCN.chm/pdf` | CHM/PDF | 自动化安装程序指南 |
| `ReadMePE2MzhCN.chm` | CHM | TIA Portal 使用须知 |
| `ReadMeSTEP734zhCN.chm` | CHM | STEP 7 说明 |
| `ReadMeSimNetzhCN.chm` | CHM | SimNet 网络说明 |
| `ReadMeTF*.chm` | CHM | Technology Functions 说明 |
| `ReadMeTIAPUPDATEzhCN.chm` | CHM | TIA Portal 更新说明 |
| `ReadMeWCC*.chm` | CHM | WinCC 说明 |

### 3. PDF参考手册 (`manual/`)

包含详细的硬件和编程手册：

| 手册名称 | 设备型号 |
|----------|---------|
| RDF302.B/RDF302_VB 手册 | CE1P3079 |
| PXC4.E16 控制器手册 | A6V11646018 |
| PXC4.M16 控制器手册 | A6V11937668 |
| PXC5.E003 控制器手册 | A6V11646020 V3 |
| PXC5.E24 控制器手册 | A6V13187283 |
| PXC7 控制器手册 | A6V12505052 |
| FB 编程模块归类 | 功能块参考 |

---

## 快速开始

### 环境要求

- **浏览器**: Chrome / Firefox / Edge / Safari (推荐现代浏览器)
- **CHM阅读**: Windows 系统自带或 CHM 阅读器
- **PDF阅读**: Adobe Reader 或任意 PDF 阅读器

### 本地浏览HTML文档

1. 克隆或下载本仓库：
```bash
git clone https://your-repo-url.git
cd ABT_Site_Help_DocumentChineseVersion
```

2. 启动本地服务器（推荐）：
```bash
# 使用 Python 内置服务器
cd HTML_Doc
python -m http.server 8080

# 或使用 Node.js
npx serve HTML_Doc
```

3. 浏览器访问：
```
http://localhost:8080/en-US/index.html    # 英文版
http://localhost:8080/zh-CN/index.html    # 中文版
```

> **注意**: 由于文档使用了 JavaScript 动态加载和 AJAX 请求，直接通过 `file://` 协议打开可能会遇到跨域限制问题，建议使用本地 HTTP 服务器。

---

## 文档翻译工具

本项目集成了 **HTML文档批量翻译系统**，可自动将英文文档翻译为中文。

详细使用方法请参阅：[`translate-skill-guide.md`](./HTML_Doc/translate-skill-guide.md)

### 核心特性

- ✅ **智能HTML解析** - 只翻译文本内容，保护代码结构
- ✅ **变量名保护** - 自动识别并保留变量名、型号代码
- ✅ **术语表管理** - 确保专业术语翻译一致性
- ✅ **多翻译后端** - 支持 Google/DeepL/有道/百度
- ✅ **批量并发处理** - 多线程加速大规模翻译
- ✅ **断点续译** - 支持中断恢复，避免重复工作

### 快速使用示例

```bash
# 使用有道翻译（国内推荐，免费）
python -m translate --backend youdao --input-dir ./en --output-dir ./zh

# 使用 Google 翻译（需代理）
python -m translate --backend google --proxy http://127.0.0.1:7890

# 测试模式（仅翻译前10个文件）
python -m translate --backend youdao --limit 10
```

---

## 产品信息

| 属性 | 详情 |
|------|------|
| **产品名称** | ABT Site (Automation Building Technologies Site) |
| **版本** | V6.0 |
| **制造商** | Siemens Schweiz AG (西门子瑞士公司) |
| **产品线** | Desigo Room Automation |
| **应用领域** | 楼宇自动化、智能建筑、HVAC控制 |
| **版权年份** | © 2014 - 2025 |

### 适用硬件

- **房间自动化控制器**: PXA系列、PXB系列、PXC系列 (PXC4, PXC5, PXC7)
- **房间自动化站**: RAZ系列、RAB系列
- **传感器/执行器**: 温湿度传感器、风阀执行器、阀门执行器
- **通信模块**: 以太网模块、BACnet/IP接口

---

## 技术栈

- **文档框架**: SCHEMA ST4 + Bootstrap 2019 v1
- **前端样式**: Bootstrap 4, Open Iconic Font
- **JavaScript库**: jQuery 3.6.3, Popper.js, Snap.svg
- **字符编码**: UTF-8
- **语言支持**: en-US, zh-CN

---

## 许可证与版权

© 2014 - 2025 Siemens Schweiz AG

本文档为西门子官方产品文档的中文翻译版本，仅供学习和参考使用。

---

## 相关链接

- [西门子官网](https://www.siemens.com)
- [西门子楼宇科技](https://buildingtechnologies.siemens.com)
- [Desigo Room Automation 产品页面](https://new.siemens.com/global/en/products/buildingtechnologies/buildingautomation/desigocc.html)
- [TIA Portal 下载](https://support.industry.siemens.com/cs/ww/en/ps/109771566)

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| V6.0 | 2025 | ABT Site V6.0 完整中文文档发布 |

---

## 联系支持

如有问题或建议，请联系：

- **西门子技术支持**: https://support.industry.siemens.com
- **产品咨询**: 联系当地西门子销售代表

---

<p align="center">
  <strong>ABT Site Help Document - Chinese Version</strong><br>
  <em>西门子 Desigo Room Automation 房间自动化系统中文帮助文档</em>
</p>
