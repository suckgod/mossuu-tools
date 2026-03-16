# Python AutoKit — Complete Documentation

Welcome to Python AutoKit! This package contains powerful automation scripts for everyday use.

## 📦 What's Included

**Version 1.0.0** — 10 automation scripts across 4 categories

### ✅ Already Available (4 scripts)

1. **smart_rename.py** — Batch file renaming
2. **duplicate_finder.py** — Find/delete duplicate files
3. **disk_alerter.py** — Disk space monitoring
4. **log_watcher.py** — Real-time log monitoring

### 🚧 Coming Soon (6 scripts)

5.  backup_rotator.py — Backup rotation
6.  csv_analyzer.py — CSV data profiling
7.  excel_formatter.py — Excel formatting
8.  json_merger.py — JSON merge tools
9.  markdown_toc.py — Markdown table of contents
10. blog_auto.py — Blog automation
11. transcript_cleaner.py — Transcript cleaning

*(All scripts will be delivered to purchasers as they are completed.)*

---

## 🚀 Quick Start

### Installation

No installation needed! Just ensure you have Python 3.6+.

```bash
# Check Python version
python3 --version  # Should be 3.6+

# Optional: install dependencies
pip3 install psutil requests
```

### Basic Usage

```bash
cd python-autokit/scripts

# 1. Batch rename files
python3 smart_rename.py "photo_{:03d}.jpg" *.jpg --dry-run

# 2. Find duplicate files
python3 duplicate_finder.py ~/Downloads --min-size 1MB --action list

# 3. Monitor disk space (daemon mode)
python3 disk_alerter.py / --threshold 85% --daemon

# 4. Watch logs for errors
python3 log_watcher.py /var/log/app.log --pattern "ERROR|FATAL" --email admin@example.com
```

See individual script `--help` for full options.

---

## 📚 Documentation

Each script includes:

- **`--help`** — Built-in usage examples
- **Inline comments** — Detailed code explanations
- **Configuration examples** — Easy customization

For questions not covered in docs, open an Issue.

---

## 🔧 Dependencies

**Required Python 3.6+** (standard library only for most scripts)

**Optional:**
- `psutil` — for disk_alerter (better cross-platform stats)
- `requests` — for webhook notifications

Install optional deps:

```bash
pip3 install psutil requests
```

---

## 💡 Support

- 📖 Read this README and script help text
- 🐛 [Open an Issue](https://github.com/suckgod/mossuu-tools/issues) for bugs
- 💬 [Discussions](https://github.com/suckgod/mossuu-tools/discussions) for questions

I respond within 24 hours.

---

## 📄 License

MIT License — see LICENSE file.

You may use these scripts personally or commercially, modify them, and redistribute. Just keep the license notice.

---

**Enjoy your automation!** 🎉

MOSSUU 🐱