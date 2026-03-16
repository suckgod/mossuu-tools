# Python 标准库版数据清洗
# 移除了 pandas 依赖，用 csv 模块

import os
import sys
import csv
from pathlib import Path

class SimpleDataCleaner:
    def __init__(self, input_dir="data/raw", output_dir="data/clean"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def clean_csv(self, filepath):
        """清洗 CSV 文件（标准库实现）"""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = []
            seen = set()

            for row in reader:
                # 删除所有值为空的列
                cleaned = {k.strip().lower(): v.strip() for k, v in row.items() if v and v.strip()}
                if cleaned:
                    # 去重：基于行内容哈希
                    row_hash = hash(frozenset(cleaned.items()))
                    if row_hash not in seen:
                        seen.add(row_hash)
                        rows.append(cleaned)

        # 写入干净文件
        if rows:
            out_path = self.output_dir / Path(filepath).name
            with open(out_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"[OK] {filepath} -> {out_path} ({len(rows)} rows)")

    def run(self):
        files = list(self.input_dir.glob("*.csv"))
        print(f"Found {len(files)} CSV file(s)")
        for f in files:
            self.clean_csv(f)

if __name__ == "__main__":
    cleaner = SimpleDataCleaner()
    cleaner.run()
