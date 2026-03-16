#!/usr/bin/env python3
"""
CSV Analyzer - Quick CSV profiling and statistics

Analyze CSV files to understand structure, quality, and content:
- Row/column counts
- Data types per column
- Missing values analysis
- Unique values count
- Numeric statistics (min/max/mean/std)
- Top frequent values
- Sample rows preview
- Export analysis report (JSON/Markdown)

Usage:
    python csv_analyzer.py data.csv
    python csv_analyzer.py data.csv --output report.json
    python csv_analyzer.py *.csv --format markdown --output-dir reports/
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter
import statistics

__version__ = "1.0.0"

class CSVAnalyzer:
    def __init__(self, csv_path: str,
                 sample_size: int = 100,
                 max_unique: int = 20,
                 output_format: str = 'json',
                 output_dir: str = None):
        self.csv_path = Path(csv_path)
        self.sample_size = sample_size
        self.max_unique = max_unique
        self.output_format = output_format.lower()
        self.output_dir = Path(output_dir) if output_dir else None

        self.metadata = {}
        self.column_stats = {}
        self.rows = []

    def read_csv(self) -> None:
        """Read CSV file and collect basic metadata"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

        self.metadata['filename'] = self.csv_path.name
        self.metadata['file_size'] = self.csv_path.stat().st_size

        with open(self.csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Detect dialect
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                has_header = sniffer.has_header(sample)
            except:
                dialect = csv.excel
                has_header = True

            reader = csv.DictReader(f, dialect=dialect)
            self.metadata['fieldnames'] = reader.fieldnames or []
            self.metadata['num_columns'] = len(self.metadata['fieldnames'])

            # Read rows
            rows = list(reader)
            self.metadata['num_rows'] = len(rows)

            # Take sample
            self.rows = rows[:self.sample_size] if len(rows) > self.sample_size else rows

    def infer_type(self, value: str) -> str:
        """Infer data type from string value"""
        if value == '' or value is None:
            return 'null'

        # Try numeric
        try:
            int(value)
            return 'integer'
        except:
            pass

        try:
            float(value)
            return 'float'
        except:
            pass

        # Try date (basic check)
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']
        for fmt in date_formats:
            try:
                from datetime import datetime
                datetime.strptime(value, fmt)
                return 'date'
            except:
                continue

        # Boolean
        lower = value.lower().strip()
        if lower in ('true', 'false', 'yes', 'no', '1', '0'):
            return 'boolean'

        return 'string'

    def analyze_column(self, col_name: str) -> Dict[str, Any]:
        """Analyze a single column"""
        values = [row.get(col_name, '') for row in self.rows if col_name in row]

        stats = {
            'name': col_name,
            'non_null_count': sum(1 for v in values if v != '' and v is not None),
            'null_count': sum(1 for v in values if v == '' or v is None),
            'unique_count': 0,
            'unique_values': [],
            'type': 'unknown',
            'numeric_stats': {},
            'top_values': []
        }

        # Calculate non-null percentage
        total = len(values)
        if total > 0:
            stats['non_null_ratio'] = stats['non_null_count'] / total
        else:
            stats['non_null_ratio'] = 0.0

        # Infer types
        types = [self.infer_type(v) for v in values if v != '' and v is not None]
        if types:
            most_common_type = Counter(types).most_common(1)[0][0]
            stats['type'] = most_common_type

        # Unique values
        cleaned_values = [v.strip() for v in values if v != '' and v is not None]
        unique_set = set(cleaned_values)
        stats['unique_count'] = len(unique_set)

        if len(unique_set) <= self.max_unique:
            stats['unique_values'] = list(unique_set)

        # Top frequent values
        if cleaned_values:
            counter = Counter(cleaned_values)
            stats['top_values'] = [(val, count) for val, count in counter.most_common(10)]

        # Numeric statistics
        if stats['type'] in ('integer', 'float'):
            numeric_vals = []
            for v in values:
                try:
                    numeric_vals.append(float(v))
                except:
                    pass

            if numeric_vals:
                stats['numeric_stats'] = {
                    'min': min(numeric_vals),
                    'max': max(numeric_vals),
                    'mean': statistics.mean(numeric_vals),
                    'median': statistics.median(numeric_vals),
                    'stdev': statistics.stdev(numeric_vals) if len(numeric_vals) > 1 else 0.0
                }

        return stats

    def analyze(self) -> None:
        """Main analysis"""
        print(f"Analyzing: {self.csv_path.name}")
        self.read_csv()

        print(f"  Rows: {self.metadata['num_rows']:,}")
        print(f"  Columns: {self.metadata['num_columns']}")

        # Analyze each column
        for col in self.metadata['fieldnames']:
            stats = self.analyze_column(col)
            self.column_stats[col] = stats

            non_null_pct = stats.get('non_null_ratio', 0) * 100
            print(f"  {col}: {stats['type']} ({non_null_pct:.1f}% non-null)")

    def generate_report(self) -> Dict[str, Any]:
        """Generate full analysis report"""
        report = {
            'metadata': self.metadata,
            'analysis_timestamp': self.get_timestamp(),
            'columns': list(self.column_stats.values())
        }
        return report

    def get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def save_report(self, report: Dict[str, Any]) -> Path:
        """Save report to file"""
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            base_name = self.csv_path.stem
        else:
            output_path = self.csv_path.parent
            base_name = f"{self.csv_path.stem}_analysis"

        if self.output_format == 'json':
            filename = f"{base_name}.json"
            output_file = (self.output_dir or self.csv_path.parent) / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        elif self.output_format == 'markdown':
            filename = f"{base_name}.md"
            output_file = (self.output_dir or self.csv_path.parent) / filename
            self.write_markdown_report(report, output_file)

        else:
            raise ValueError(f"Unsupported format: {self.output_format}")

        print(f"\nReport saved: {output_file}")
        return output_file

    def write_markdown_report(self, report: Dict[str, Any], output_file: Path):
        """Write report in Markdown format"""
        meta = report['metadata']

        lines = [
            f"# CSV Analysis Report: {meta['filename']}",
            "",
            "## Metadata",
            f"- **File size**: {meta['file_size']:,} bytes",
            f"- **Rows**: {meta['num_rows']:,}",
            f"- **Columns**: {meta['num_columns']}",
            f"- **Analyzed at**: {report['analysis_timestamp']}",
            "",
            "## Column Analysis",
            "",
            "| Column | Type | Non-Null % | Unique | Numeric Stats |",
            "|--------|------|------------|--------|---------------|"
        ]

        for col in report['columns']:
            non_null_pct = col.get('non_null_ratio', 0) * 100
            unique = col['unique_count']
            numeric = col.get('numeric_stats', {})

            if numeric:
                numeric_str = f"min={numeric['min']:.2g}, max={numeric['max']:.2g}, mean={numeric['mean']:.2g}"
            else:
                numeric_str = "-"

            lines.append(f"| {col['name']} | {col['type']} | {non_null_pct:.1f}% | {unique} | {numeric_str} |")

        lines.extend([
            "",
            "## Top Values per Column",
            ""
        ])

        for col in report['columns']:
            lines.append(f"### {col['name']}")
            if col['top_values']:
                for val, count in col['top_values'][:10]:
                    lines.append(f"- `{val}` ({count})")
            else:
                lines.append("- (no data)")
            lines.append("")

        output_file.write_text('\n'.join(lines), encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(
        description="CSV Analyzer - Quick CSV profiling and statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single CSV (output JSON)
  %(prog)s data.csv

  # Output Markdown report to specific directory
  %(prog)s data.csv --format markdown --output-dir reports/

  # Analyze multiple CSVs with custom sample size
  %(prog)s *.csv --sample 500 --output-dir analysis_reports/

  # Limit unique values display (reduces output size)
  %(prog)s big_data.csv --max-unique 50

Features:
  - Auto-detects CSV dialect and delimiter
  - Infers data types (integer, float, date, boolean, string)
  - Calculates missing value statistics
  -Reports numeric columns with mean/std/min/max
  - Shows top frequent values per column
  - Exports JSON or Markdown reports
      """
    )
    parser.add_argument(
        "csv_files",
        nargs="+",
        help="CSV file(s) to analyze"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=100,
        help="Number of rows to sample for analysis (default: 100, use more for small files)"
    )
    parser.add_argument(
        "--max-unique",
        type=int,
        default=20,
        help="Max unique values to include in report (default: 20)"
    )
    parser.add_argument(
        "--format",
        choices=['json', 'markdown'],
        default='json',
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save reports (default: same as CSV)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"csv_analyzer {__version__}"
    )

    args = parser.parse_args()

    if not args.csv_files:
        parser.error("At least one CSV file required")

    success_count = 0
    for csv_file in args.csv_files:
        try:
            analyzer = CSVAnalyzer(
                csv_path=csv_file,
                sample_size=args.sample,
                max_unique=args.max_unique,
                output_format=args.format,
                output_dir=args.output_dir
            )
            analyzer.analyze()
            report = analyzer.generate_report()
            analyzer.save_report(report)
            success_count += 1
        except Exception as e:
            print(f"Error analyzing {csv_file}: {e}", file=sys.stderr)

    print(f"\nCompleted: {success_count}/{len(args.csv_files)} files analyzed successfully")
    if success_count < len(args.csv_files):
        sys.exit(1)

if __name__ == "__main__":
    main()
