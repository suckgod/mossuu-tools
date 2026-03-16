# Python AutoKit — $19.99

**10 powerful automation scripts for developers, data scientists, and content creators**

[Buy Now](#) | [View on GitHub](https://github.com/suckgod/mossuu-tools)

---

## 📦 What's Inside

### Category 1: File Management

#### 1. `smart_rename.py`
**Batch rename files with patterns**

**Use cases:**
- Rename photos: `IMG_001.jpg` → `vacation_001.jpg`
- Organize downloads: add dates, sequential numbers
- Convert file naming conventions

**Features:**
- Regex pattern support
- Preview before applying
- Undo capability
- Dry-run mode

```bash
python smart_rename.py --pattern "vacation_{:03d}.jpg" --files *.jpg
```

---

#### 2. `duplicate_finder.py`
**Find and manage duplicate files**

**Use cases:**
- Clean up duplicate photos/downloads
- Free up disk space
- Organize scattered backups

**Features:**
- Multiple hash algorithms (MD5, SHA1, SHA256)
- Size threshold filtering
- Interactive deletion/archival
- Report generation

```bash
python duplicate_finder.py /path/to/folder --min-size 1MB --action list
```

---

#### 3. `backup_rotator.py`
**Automatic backup rotation**

**Use cases:**
- Keep last N backups, auto-delete old ones
- Daily/weekly/monthly backup strategies
- Database dump rotation

**Features:**
- Time-based retention policies
- Multiple backup directories
- Email/desktop notifications
- Dry-run preview

```bash
python backup_rotator.py --backup-dir /backups --keep-daily 7 --keep-weekly 4
```

---

### Category 2: Data Processing

#### 4. `csv_analyzer.py`
**Quick CSV data analysis and statistics**

**Use cases:**
- Understand new datasets quickly
- Generate summary reports
- Data quality assessment

**Features:**
- Row/column count, missing values, data types
- Numeric column statistics (mean, median, std)
- Categorical column frequency
- Export to JSON/HTML

```bash
python csv_analyzer.py data.csv --output report.html
```

---

#### 5. `excel_formatter.py`
**Standardize Excel table formatting**

**Use cases:**
- Clean up messy exports
- Apply consistent styling
- Prepare data for presentations

**Features:**
- Column width auto-fit
- Header styling (bold, background color)
- Number format standardization
- Conditional formatting rules

```bash
python excel_formatter.py messy.xlsx --output clean.xlsx --header-color "#4F81BD"
```

---

#### 6. `json_merger.py`
**Merge and deduplicate JSON files**

**Use cases:**
- Combine API paginated results
- Merge export files from multiple sources
- Consolidate configuration files

**Features:**
- Array concatenation with deduplication
- Deep merge for nested objects
- Key-based deduplication
- Preserve ordering

```bash
python json_merger.py part1.json part2.json --output combined.json --dedupe-by id
```

---

### Category 3: Content Creation

#### 7. `markdown_toc.py`
**Auto-generate Markdown table of contents**

**Use cases:**
- Enhance long READMEs
- Add TOC to documentation
- Maintain up-to-date TOC automatically

**Features:**
- Detects headings up to H6
- Customizable indentation
- GitHub Flavored Markdown support
- Skip first N headings option

```bash
python markdown_toc.py README.md --max-depth 3 --insert-after "# Introduction"
```

---

#### 8. `blog_auto.py`
**Blog post automation (multi-platform)**

**Use cases:**
- Cross-post to Medium/Dev.to/WordPress
- Scheduled publishing
- Format conversion (Markdown → HTML)

**Features:**
- API integrations (WordPress REST, Ghost, Medium)
- Front matter handling (YAML/TOML)
- Image upload & optimization
- Publish scheduling

```bash
python blog_auto.py post.md --platform medium --draft
```

---

#### 9. `transcript_cleaner.py`
**Clean up subtitles and transcripts**

**Use cases:**
- Remove filler words (um, uh)
- Normalize timestamps
- Merge fragmented sentences

**Features:**
- Multiple subtitle formats (SRT, VTT)
- Silent segment removal
- Word/phrase filtering
- Export to plain text

```bash
python transcript_cleaner.py lecture.srt --remove-fillers --output cleaned.txt
```

---

### Category 4: System Monitoring

#### 10. `log_watcher.py`
**Log file monitoring and alerting**

**Use cases:**
- Watch error logs and notify
- Track application activity
- Detect anomalies in real-time

**Features:**
- Pattern matching (regex)
- Email/desktop/Slack notifications
- Stateful tracking (avoid duplicate alerts)
- Rotation handling (logrotate)

```bash
python log_watcher.py /var/log/app/error.log --pattern "ERROR|FATAL" --email admin@example.com
```

---

#### 11. `disk_alerter.py`
**Disk space monitoring**

**Use cases:**
- Prevent "disk full" surprises
- Monitor multiple drives
- Trend analysis

**Features:**
- Threshold-based alerts (%, absolute GB)
- Multi-disk support
- History logging
- Email/Slack/Telegram notifications

```bash
python disk_alerter.py --threshold 90% --check-interval 3600 --email admin@example.com
```

---

*Note: Scripts marked ⏳ are in development and will be delivered upon purchase.*

---

## 🎯 Who Is This For?

- **Developers** — Save time on boilerplate tasks
- **Data Scientists** — Quick data profiling & cleaning
- **Writers/Bloggers** — Automate publishing workflow
- **Sysadmins** — Monitor logs and disk space
- **Productivity Nerds** — Love automating the boring stuff

---

## 📋 What You Get

- ✅ **Complete source code** — Well-commented, production-ready
- ✅ **Configuration templates** — Customize quickly
- ✅ **Bilingual documentation** — English + Chinese
- ✅ **30-day support** — Via GitHub Issues
- ✅ **Lifetime updates** — Free as I add features
- ✅ **Commercial license** — Use in your projects

---

## 💰 Pricing & Purchase

**Price:** **$19.99** (one-time, lifetime)

**Payment options:**
- GitHub Sponsors (one-time)
- Buy Me a Coffee
- PayPal

**After purchase:**
1. I'll send a download link (ZIP with all scripts)
2. You can star the repo as a token of appreciation
3. Open an issue if you need help — I'll respond within 24h

---

## ❓ FAQ

**Q: Do I need Python installed?**  
A: Yes, Python 3.6+ (most systems already have it). Some scripts may require `pandas` — instructions included.

**Q: Can I modify the scripts?**  
A: Absolutely! MIT license — modify, adapt, use commercially.

**Q: What if a script doesn't work on my OS?**  
A: Open an issue, I'll help debug. Most scripts are cross-platform.

**Q: Are updates really free forever?**  
A: Yes. One-time payment, all future updates included.

---

## 📬 Contact

- **GitHub Issues:** [Open an issue](https://github.com/suckgod/mossuu-tools/issues)
- **Email:** Via GitHub (if you prefer direct)

---

<div align="center">

**Ready to automate? Get Python AutoKit now!**

[![Buy Now](https://img.shields.io/badge/-Buy%20Now%20$19.99-ff69b4?style=for-the-badge)](https://github.com/suckgod/mossuu-tools)

</div>