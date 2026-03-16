#!/usr/bin/env python3.12
"""
DataCleaner - Excel/CSV 数据清洗工具
批量处理数据文件，标准化格式
"""

import pandas as pd
import glob
import os

class DataCleaner:
    def __init__(self, input_dir="data/raw", output_dir="data/clean"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def process_csv(self, filepath):
        """Process single CSV file"""
        df = pd.read_csv(filepath)

        # Cleaning operations
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        df = df.dropna(how="all")
        df = df.drop_duplicates()

        output_path = os.path.join(self.output_dir, os.path.basename(filepath))
        df.to_csv(output_path, index=False)
        print(f"[OK] {filepath} -> {output_path} ({len(df)} rows)")

    def process_excel(self, filepath):
        """Process single Excel file"""
        df = pd.read_excel(filepath)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        df = df.dropna(how="all").drop_duplicates()

        output_path = os.path.join(self.output_dir, os.path.basename(filepath).replace(".xlsx", ".csv"))
        df.to_csv(output_path, index=False)
        print(f"[OK] {filepath} -> {output_path} ({len(df)} rows)")

    def run(self):
        """Process all data files"""
        csv_files = glob.glob(os.path.join(self.input_dir, "*.csv"))
        excel_files = glob.glob(os.path.join(self.input_dir, "*.xlsx"))

        print(f"Found {len(csv_files)} CSV, {len(excel_files)} Excel files")

        for f in csv_files:
            self.process_csv(f)

        for f in excel_files:
            self.process_excel(f)

        print(f"\nDone! Cleaned files in {self.output_dir}/")

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.run()
