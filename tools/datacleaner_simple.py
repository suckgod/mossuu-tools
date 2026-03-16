#!/usr/bin/env python3
"""
DataCleaner - CSV data cleaning tool (no pandas required)
"""

import csv
import os
import glob

class DataCleaner:
    def __init__(self, input_dir="data/raw", output_dir="data/clean"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def clean_csv(self, filepath):
        """Clean a CSV file"""
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Strip whitespace from keys and values
                cleaned = {k.strip().lower().replace(' ', '_'): (v.strip() if v else '')
                          for k, v in row.items()}
                # Skip completely empty rows
                if any(v for v in cleaned.values()):
                    rows.append(cleaned)

        # Remove exact duplicates
        unique_rows = []
        seen = set()
        for row in rows:
            row_tuple = tuple(sorted(row.items()))
            if row_tuple not in seen:
                seen.add(row_tuple)
                unique_rows.append(row)

        output_path = os.path.join(self.output_dir, os.path.basename(filepath))
        if unique_rows:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = unique_rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(unique_rows)
            print(f"[OK] {filepath} -> {output_path} ({len(unique_rows)} rows)")
        else:
            print(f"[WARN] {filepath}: no valid rows after cleaning")

    def run(self):
        """Process all CSV files"""
        csv_files = glob.glob(os.path.join(self.input_dir, "*.csv"))

        print(f"Found {len(csv_files)} CSV files")

        if not csv_files:
            print("No files to process. Add CSV files to data/raw/")
            return

        for f in csv_files:
            self.clean_csv(f)

        print(f"\nDone! Clean files in {self.output_dir}/")

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        cleaner = DataCleaner(input_dir, output_dir)
    else:
        cleaner = DataCleaner()
    cleaner.run()
