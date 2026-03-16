# Getting Started with MOSSUU Tools

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Duan-mua/mossuu-tools.git
cd mossuu-tools
```

### 2. Install dependencies (optional)
```bash
# For DataCleaner with pandas (recommended)
pip3 install pandas openpyxl

# Or use the simple version without dependencies
# (tools/simple_datacleaner.py)
```

### 3. Run tools

#### AutoNote - Organize your notes
```bash
python3 tools/autonote.py /path/to/your/notes
```
This will scan all `.md` files, categorize them, remove duplicates, and generate an `INDEX.md`.

#### ReportGen - Daily report generator
```bash
python3 tools/reportgen.py tools/config.json
```
Creates a daily markdown report in `reports/` folder.

#### DataCleaner - Clean CSV/Excel data
```bash
python3 tools/datacleaner.py
```
Processes all files in `data/raw/` and outputs cleaned versions to `data/clean/`.

---

## Products

### Python AutoKit - $19.99
10 ready-to-use automation scripts. See [products/python-autokit-product.md](products/python-autokit-product.md)

### AI Productivity eBook - $9.99
《AI生产力实战》- Practical guide to AI-powered productivity. See [products/ai-productivity-ebook.md](products/ai-productivity-ebook.md)

### Personal Auto-Assistant - $9.99/month
Subscription service: 10 daily task calls, data processing, content creation.

---

## Support

- GitHub Issues: [Create an issue](https://github.com/Duan-mua/mossuu-tools/issues)
- Buy Me a Coffee: COMING SOON
- Email: via GitHub Discussions

---

## License

MIT License - see LICENSE file for details.
