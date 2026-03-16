# MOSSUU 自动化工具集 - 快速开始

一键安装所有依赖并开始使用。

## 📦 包含工具

| 工具 | 描述 | 状态 |
|------|------|------|
| AutoNote | 智能笔记整理（分类+去重+索引） | ✅ 可用 |
| SimpleDataCleaner | CSV 数据清洗（纯 Python 标准库） | ✅ 可用 |
| DataCleaner | 高级数据清洗（CSV+Excel，需 pandas） | ✅ 可用 |
| ReportGen | 每日报告生成器（Git + 日历） | ✅ 可用 |

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/Duan-mua/mossuu-tools.git
cd mossuu-tools
```

### 2. 安装依赖（可选）

**基础功能**（无需额外依赖）：
- AutoNote、SimpleDataCleaner 开箱即用

**高级功能**：
```bash
pip3 install pandas openpyxl
```

### 3. 运行工具

**AutoNote** - 整理笔记：
```bash
python3 tools/autonote.py /path/to/notes
# 生成 INDEX.md
```

**SimpleDataCleaner** - 清洗 CSV：
```bash
python3 tools/simple_datacleaner.py
# 输入: data/raw/*.csv → 输出: data/clean/*.csv
```

**DataCleaner** - 清洗 CSV + Excel：
```bash
python3 tools/datacleaner.py
# 支持 .csv 和 .xlsx
```

**ReportGen** - 生成日报：
```bash
python3 tools/reportgen.py
# 输出: reports/report_YYYY-MM-DD.md
```

## 📁 目录结构

```
mossuu-tools/
├── tools/              # 所有脚本
│   ├── autonote.py
│   ├── simple_datacleaner.py
│   ├── datacleaner.py
│   ├── reportgen.py
│   └── config.json
├── tests/              # 测试数据
├── data/               # 数据输入/输出
│   ├── raw/
│   └── clean/
├── reports/            # 生成的报告
└── products/           # 付费产品介绍
```

## 💰 付费产品

- **Python AutoKit** - $19.99（10个高级脚本）
- **《AI生产力实战》电子书** - $9.99

[查看详情](products/)

## 🤝 支持

有问题？开 GitHub Issue 或赞助我喝咖啡 ☕

---

**Created by MOSSUU** 🐱 | [Buy Me a Coffee](https://buymeacoffee.com/mossuu)
