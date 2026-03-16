#!/usr/bin/env python3
"""
ReportGen - 每日报告自动生成器
从多种数据源生成汇总报告
"""

import json
import os
from datetime import datetime, timedelta

class ReportGenerator:
    def __init__(self, config_file="config.json"):
        with open(config_file) as f:
            self.config = json.load(f)

    def gather_data(self):
        """从各数据源收集数据"""
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sources": []
        }

        # 1. Git 提交统计
        if "git" in self.config["sources"]:
            git_data = self._get_git_stats()
            data["sources"].append(git_data)

        # 2. 系统资源
        if "system" in self.config["sources"]:
            sys_data = self._get_system_info()
            data["sources"].append(sys_data)

        # 3. 日历事件
        if "calendar" in self.config["sources"]:
            cal_data = self._get_calendar_events()
            data["sources"].append(cal_data)

        return data

    def _get_git_stats(self):
        """获取 Git 仓库统计"""
        os.system("git log --since='1 day ago' --oneline > /tmp/git_today.txt 2>/dev/null")
        commits = len(open("/tmp/git_today.txt").readlines()) if os.path.exists("/tmp/git_today.txt") else 0
        return {
            "type": "git",
            "commits_today": commits,
            "summary": f"今日提交 {commits} 次"
        }

    def _get_system_info(self):
        """获取系统信息（简化版）"""
        return {
            "type": "system",
            "disk_usage": "N/A",  # 可扩展
            "memory": "N/A"
        }

    def _get_calendar_events(self):
        """获取日历事件（简化版）"""
        return {
            "type": "calendar",
            "events_today": 0,
            "upcoming": []
        }

    def generate_markdown(self, data):
        """生成 Markdown 格式报告"""
        lines = [
            f"# 每日报告 - {data['date']}",
            "",
            "## 📊 概览",
            ""
        ]

        for source in data["sources"]:
            lines.append(f"### {source['type'].upper()}")
            if source["type"] == "git":
                lines.append(f"- {source['summary']}")
            lines.append("")

        lines.extend([
            "## 📝 备注",
            "- 自动生成，请补充具体工作内容",
            "",
            "---",
            "*由 MOSSUU 自动化生成*"
        ])

        return "\n".join(lines)

    def save_report(self, markdown):
        """保存报告文件"""
        filename = f"reports/report_{datetime.now().strftime('%Y-%m-%d')}.md"
        os.makedirs("reports", exist_ok=True)
        with open(filename, "w") as f:
            f.write(markdown)
        print(f"报告已保存: {filename}")
        return filename

    def run(self):
        data = self.gather_data()
        md = self.generate_markdown(data)
        return self.save_report(md)

if __name__ == "__main__":
    import sys
    config = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    gen = ReportGenerator(config)
    gen.run()
