#!/usr/bin/env python3
"""
DataCleaner Lite - 纯标准库版本，无需第三方依赖
支持 CSV 文件的简单清洗
"""

import csv
import os
import glob

class DataCleanerLite:
    def __init__(self, input_dir="data/raw", output_dir="data/clean"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def clean_csv(self, filepath):
        """清洗 CSV 文件"""
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 去除空行（所有值都为空）
                if any(val.strip() for val in row.values() if val):
                    # 去除列名空格、转小写
                    cleaned = {k.strip().lower().replace(' ', '_'): v.strip() for k, v in row.items()}
                    rows.append(cleaned)

        # 去重（基于所有字段的 tuple）
        unique_rows = []
        seen = set()
        for row in rows:
            key = tuple(sorted(row.items()))
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)

        return unique_rows

    def process_file(self, filepath):
        """处理单个文件"""
        rows = self.clean_csv(filepath)
        if not rows:
            print(f"⚠ {filepath}: 无有效数据")
            return 0

        # 获取列名
        fieldnames = list(rows[0].keys())

        output_name = os.path.basename(filepath).replace('.csv', '_clean.csv')
        output_path = os.path.join(self.output_dir, output_name)

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"[OK] {filepath} -> {output_path} ({len(rows)} rows)")
        return len(rows)

    def run(self):
        """运行"""
        csv_files = glob.glob(os.path.join(self.input_dir, "*.csv"))
        print(f"Found {len(csv_files)} CSV files")

        total = 0
        for f in csv_files:
            total += self.process_file(f)

        print(f"\nDone! {total} rows processed. Output: {self.output_dir}/")
        return total

if __name__ == "__main__":
    cleaner = DataCleanerLite()
    cleaner.run()
