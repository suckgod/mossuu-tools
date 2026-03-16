# 使用说明

## 快速开始

1. 克隆或下载本项目
2. 确保已安装 Python 3.8+
3. 将你的笔记文件夹路径作为参数运行：

```bash
python tools/autonote.py /path/to/your/notes
```

## 功能说明

### AutoNote - 智能笔记整理
- 自动扫描所有 `.md` 文件
- 根据关键词分类（ideas, tasks, projects, reference, daily）
- 去重（基于内容前100字符）
- 生成 `INDEX.md` 索引文件

### ReportGen - 每日报告生成器
（待开发）

### DataCleaner - 数据清洗工具
（待开发）

## 配置

可以修改 `NoteOrganizer.categories` 字典来自定义分类规则。

## License

MIT - 可自由使用、修改、分发。
