# Python Dependencies for AutoKit

This document lists all Python package dependencies for the AutoKit scripts, both required and optional.

## 📋 Summary Table

| Script | Required Packages | Optional Packages |
|--------|-------------------|-------------------|
| `smart_rename.py` | None (stdlib only) | - |
| `duplicate_finder.py` | None (stdlib only) | - |
| `backup_rotator.py` | None (stdlib only) | - |
| `csv_analyzer.py` | None (stdlib only) | - |
| `json_merger.py` | None (stdlib only) | - |
| `markdown_toc.py` | None (stdlib only) | - |
| `transcript_cleaner.py` | None (stdlib only) | - |
| `disk_alerter.py` | **psutil** | **requests** (for webhook) |
| `log_watcher.py` | None (stdlib only) | **requests** (for webhook) |
| `excel_formatter.py` | **pandas**, **openpyxl** | - |
| `blog_auto.py` | None (stdlib only) | **requests**, **PyYAML**, **Pillow** |

---

## 🐍 Install All Dependencies

```bash
# Required packages only
pip install psutil pandas openpyxl

# Optional packages (for full feature set)
pip install requests pyyaml pillow
```

Or create a `requirements.txt`:

```txt
# Required
psutil>=5.0.0
pandas>=1.0.0
openpyxl>=3.0.0

# Optional (blog_auto + notifications)
requests>=2.0.0
pyyaml>=5.0
pillow>=8.0.0
```

Install with:

```bash
pip install -r requirements.txt
```

---

## 📦 Package Details

### Core Dependencies

#### `psutil`
- **Used by**: `disk_alerter.py`
- **Purpose**: Cross-platform system monitoring (disk usage)
- **Install**: `pip install psutil`
- **Supported**: Python 3.6+, Linux/macOS/Windows

#### `pandas`
- **Used by**: `excel_formatter.py`
- **Purpose**: Excel/CSV data manipulation
- **Install**: `pip install pandas`
- **Note**: Also requires `openpyxl` for Excel files
- **Minimum version**: 1.0.0

#### `openpyxl`
- **Used by**: `excel_formatter.py`
- **Purpose**: Read/write Excel `.xlsx` files, styling support
- **Install**: `pip install openpyxl`
- **Minimum version**: 3.0.0

### Optional Dependencies

#### `requests`
- **Used by**: `disk_alerter.py` (webhook), `log_watcher.py` (webhook), `blog_auto.py` (API calls)
- **Purpose**: HTTP requests for notifications and blog publishing
- **Install**: `pip install requests`
- **Scripts without it**: Disk alerter and log watcher still work for file-based/SMTP operations

#### `PyYAML`
- **Used by**: `blog_auto.py`
- **Purpose**: Parse Markdown frontmatter
- **Install**: `pip install pyyaml`
- **Fallback**: Without it, only basic frontmatter parsing (no YAML)

#### `Pillow` (PIL)
- **Used by**: `blog_auto.py`
- **Purpose**: Image processing/upload to WordPress
- **Install**: `pip install pillow`
- **Scripts without it**: blog_auto still works, just no image upload feature

---

## 🧪 Testing Dependencies

For running the test suite:

```bash
# No additional packages required for smoke tests
python -m unittest tests.test_autokit_smoke

# Optional: pytest for advanced test runs
pip install pytest
pytest tests/
```

---

## 📝 Minimum Python Version

All scripts are compatible with **Python 3.6+**.

Recommended: Python 3.8+ for best performance and features.

---

## 🚨 Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"
```bash
pip install pandas openpyxl
```

### "ModuleNotFoundError: No module named 'psutil'"
```bash
pip install psutil
```

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests
```

### Script works but without feature X
Check which optional dependency is missing. The script will print a warning if you try to use a feature that requires an uninstalled package.

---

## 🔒 License

All dependencies are permissive licenses (MIT, Apache 2.0, BSD).
