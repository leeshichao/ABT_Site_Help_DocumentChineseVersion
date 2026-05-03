# 文档翻译系统 - 快速使用指南

## 重要提示

**必须从项目根目录运行**：

```bash
cd d:\dve\ABT-test\Doc\zh
python -m translate [选项]
```

---

## 快速命令

### 1. 检查环境
```bash
python -m translate --check-only
```

### 2. 扫描文件统计
```bash
python -m translate --dry-run --limit 5
```

### 3. 翻译前5个文件测试
```bash
# MyMemory翻译（推荐，默认选项）
python -m translate --limit 5 --no-banner --backend mymemory

# 有道翻译（备用）
python -m translate --limit 5 --no-banner
```

### 4. 完整翻译（建议夜间运行）
```bash
python -m translate --workers 4 --no-banner --backend mymemory
```

---

## 翻译后端对比

| 后端 | 命令 | 中国大陆 | 速度 | 推荐度 |
|------|------|---------|------|--------|
| **MyMemory** | `--backend mymemory` | ✅ 可用 | 中等 | ⭐⭐⭐⭐⭐ |
| 有道翻译 | `--backend youdao` | ⚠️ 不稳定 | 快 | ⭐⭐⭐ |
| Google | `--backend google` | ❌ 需代理 | 快 | ⭐⭐⭐⭐ |
| DeepL | `--backend deepl-free` | ❌ 需代理 | 快 | ⭐⭐⭐⭐⭐ |

---

## 项目统计

- 📊 **总文件数**: 2,274 个 HTML
- 📦 **总大小**: 31.85 MB
- 📝 **术语表**: 2520 条（HVAC/BACnet/Siemens）

---

## 文件位置

```
d:\dve\ABT-test\Doc\zh\
├── translate/                  # 翻译工具
│   ├── __main__.py            # 入口点
│   ├── main.py                # 主程序
│   ├── translator_engine.py    # 翻译引擎
│   ├── orchestrator.py        # 批量调度
│   ├── html_parser.py         # HTML解析
│   ├── glossary.csv            # 术语表
│   ├── README.md              # 完整文档
│   └── QUICKSTART.md          # 本文件
│
├── en-US/                     # 输入（英文）
└── zh-CN/                     # 输出（中文，自动创建）
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| `No module named 'translate'` | 必须从 `zh` 目录运行 |
| 翻译失败 | 尝试更换后端：`--backend mymemory` |
| Google无法使用 | 国内需要VPN，建议用有道翻译 |
| 中断后继续 | 直接重新运行，自动从断点继续 |

---

## 下一步

1. 先运行 `--check-only` 确认环境正常
2. 运行 `--dry-run --limit 5` 查看文件列表
3. 运行 `--limit 5` 翻译5个文件测试效果
4. 确认质量满意后，启动完整翻译
