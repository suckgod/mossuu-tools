# Duplicate Finder Demo Data

This directory contains sample files to test the duplicate finder.

## Setup

```bash
# Copy demo files to a test location
cp -r tests/test_data /tmp/dupe_test

# Run duplicate finder (dry run)
python tools/duplicate_finder.py /tmp/dupe_test --dry-run

# Generate report
python tools/duplicate_finder.py /tmp/dupe_test --report /tmp/duplicates.csv
```

## Expected Results

Should find:
- `photos/cat1.jpg` and `photos/cat1-copy.jpg` (duplicate)
- `docs/report_v1.pdf` and `docs/report_v2.pdf` (same content, different names)
- `backup/fileA.bak` in multiple subdirectories (identical backups)

## Files

- `photos/` - Sample images with duplicates
- `docs/` - Documents with version duplicates
- `backup/` - Backup directories containing redundant files
