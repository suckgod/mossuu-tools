#!/usr/bin/env python3
"""
JSON Merger - Merge and deduplicate JSON files

Combine multiple JSON files with smart merging:
- Merge arrays (union or intersection)
- Merge objects (deep merge, overwrite or combine)
- Remove duplicates (by key or entire object comparison)
- Handle nested structures
- Support different file encodings
- Validate JSON before merging
- Output to file or stdout

Usage:
    python json_merger.py file1.json file2.json file3.json -o merged.json
    python json_merger.py *.json --mode union --deduplicate --key "id"
    python json_merger.py config1.json config2.json --mode merge --output final.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from collections.abc import Mapping, Sequence

__version__ = "1.0.0"

class JSONMerger:
    def __init__(self, mode: str = 'union',
                 deduplicate: bool = False,
                 dedup_key: str = None,
                 deep_merge: bool = False,
                 pretty: bool = False,
                 encoding: str = 'utf-8'):
        self.mode = mode  # 'union', 'intersection', 'merge'
        self.deduplicate = deduplicate
        self.dedup_key = dedup_key
        self.deep_merge = deep_merge
        self.pretty = pretty
        self.encoding = encoding
        self.stats = {
            'files_processed': 0,
            'items_before': 0,
            'items_after': 0,
            'duplicates_removed': 0
        }

    def load_json(self, filepath: Path) -> Any:
        """Load JSON from file with error handling"""
        try:
            with open(filepath, 'r', encoding=self.encoding) as f:
                data = json.load(f)
            self.stats['files_processed'] += 1
            return data
        except UnicodeDecodeError:
            # Try different encoding
            with open(filepath, 'r', encoding='latin-1') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")

    def is_primitive(self, obj: Any) -> bool:
        """Check if object is primitive (comparable for deduplication)"""
        return isinstance(obj, (str, int, float, bool, type(None)))

    def get_dedup_key(self, item: Any, key: str = None) -> Any:
        """Get deduplication key for an item"""
        if key:
            # Navigate nested key (dot notation not supported, simple key only)
            if isinstance(item, Mapping) and key in item:
                return item[key]
            return None
        else:
            # Use entire item if primitive, else string hash
            if self.is_primitive(item):
                return item
            return json.dumps(item, sort_keys=True)

    def deduplicate_list(self, items: List[Any]) -> List[Any]:
        """Remove duplicates from list while preserving order"""
        seen = set()
        result = []
        removed = 0

        for item in items:
            key = self.get_dedup_key(item, self.dedup_key)
            if key not in seen:
                seen.add(key)
                result.append(item)
            else:
                removed += 1

        self.stats['duplicates_removed'] += removed
        return result

    def merge_arrays(self, arrays: List[List[Any]]) -> List[Any]:
        """Merge multiple arrays according to mode"""
        if self.mode == 'union':
            merged = []
            for arr in arrays:
                merged.extend(arr)
        elif self.mode == 'intersection':
            if not arrays:
                return []
            # Find common elements across all arrays
            merged = list(arrays[0])
            for arr in arrays[1:]:
                merged = [x for x in merged if x in arr]
        else:
            raise ValueError(f"Unknown mode for arrays: {self.mode}")

        if self.deduplicate:
            merged = self.deduplicate_list(merged)

        return merged

    def deep_merge_objects(self, obj1: Dict, obj2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = obj1.copy()
        for key, value in obj2.items():
            if key in result and isinstance(result[key], Mapping) and isinstance(value, Mapping):
                result[key] = self.deep_merge_objects(result[key], value)
            else:
                result[key] = value
        return result

    def merge_objects(self, objects: List[Dict]) -> Dict:
        """Merge multiple objects"""
        if not objects:
            return {}

        if self.deep_merge:
            merged = {}
            for obj in objects:
                merged = self.deep_merge_objects(merged, obj)
            return merged
        else:
            # Simple merge: later objects overwrite earlier ones
            merged = {}
            for obj in objects:
                merged.update(obj)
            return merged

    def merge_data(self, files_data: List[Any]) -> Any:
        """Merge data from multiple files"""
        self.stats['items_before'] = sum(
            len(d) if isinstance(d, list) else 1 for d in files_data
        )

        # Determine data type from first file
        if not files_data:
            return None

        first_type = type(files_data[0])

        if isinstance(files_data[0], list):
            # Merge arrays
            result = self.merge_arrays(files_data)
        elif isinstance(files_data[0], Mapping):
            # Merge objects
            result = self.merge_objects(files_data)
        else:
            # Single values, return last one
            result = files_data[-1]

        self.stats['items_after'] = len(result) if isinstance(result, (list, dict)) else 1
        return result

    def process_files(self, input_files: List[Path]) -> Any:
        """Load and merge multiple files"""
        files_data = []
        for filepath in input_files:
            data = self.load_json(filepath)
            files_data.append(data)

        return self.merge_data(files_data)

    def save_output(self, data: Any, output_path: Path = None):
        """Save merged data"""
        indent = 2 if self.pretty else None

        if output_path:
            with open(output_path, 'w', encoding=self.encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            print(f"✓ Saved to: {output_path}")
        else:
            print(json.dumps(data, indent=indent, ensure_ascii=False))

    def print_stats(self):
        """Print processing statistics"""
        print("\n📊 Merge Statistics:")
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  Items before:    {self.stats['items_before']}")
        print(f"  Items after:     {self.stats['items_after']}")
        if self.deduplicate:
            print(f"  Duplicates removed: {self.stats['duplicates_removed']}")

def main():
    parser = argparse.ArgumentParser(
        description="JSON Merger - Merge and deduplicate JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge multiple array files into one (union)
  %(prog)s data1.json data2.json data3.json -o all.json

  # Merge and deduplicate by 'id' field
  %(prog)s users*.json --deduplicate --key "id" -o users_merged.json

  # Deep merge configuration objects
  %(prog)s config1.json config2.json --mode merge --deep-merge -o final_config.json

  # Pretty print merged result to stdout
  %(prog)s part1.json part2.json --mode union --pretty | less

  # Intersection (items present in ALL files)
  %(prog)s lists/*.json --mode intersection -o common.json

Notes:
  - Modes:
    * union: all items from all files (default)
    * intersection: only items present in every file (arrays only)
    * merge: deep/overwrite merge for objects
  - Deduplication works on arrays; for objects, use deep merge
  - Key-based deduplication: extracts item[key] as uniqueness identifier
  - Non-primitive items use JSON string comparison
      """
    )
    parser.add_argument(
        "input_files",
        nargs="+",
        help="JSON files to merge"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--mode",
        choices=['union', 'intersection', 'merge'],
        default='union',
        help="Merge mode: union (default), intersection, or merge (for objects)"
    )
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Remove duplicate items from arrays"
    )
    parser.add_argument(
        "--key",
        help="Deduplication key (field name) for objects in arrays"
    )
    parser.add_argument(
        "--deep-merge",
        action="store_true",
        help="For object merge mode: recursively merge nested objects instead of overwrite"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation"
    )
    parser.add_argument(
        "--encoding",
        default='utf-8',
        help="File encoding (default: utf-8)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"json_merger {__version__}"
    )

    args = parser.parse_args()

    merger = JSONMerger(
        mode=args.mode,
        deduplicate=args.deduplicate,
        dedup_key=args.key,
        deep_merge=args.deep_merge,
        pretty=args.pretty,
        encoding=args.encoding
    )

    try:
        input_paths = [Path(f) for f in args.input_files]
        merged_data = merger.process_files(input_paths)
        output_path = Path(args.output) if args.output else None

        if merged_data is None:
            print("No data to merge (empty input)", file=sys.stderr)
            sys.exit(1)

        merger.save_output(merged_data, output_path)
        merger.print_stats()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
