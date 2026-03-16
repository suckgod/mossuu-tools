#!/bin/bash
# Quick setup script for MOSSUU Tools

echo "Setting up MOSSUU Tools..."

# Create necessary directories
mkdir -p tests/notes tests/data/raw tests/data/clean reports

# Create sample config for ReportGen
cat > tools/config.json << 'EOF'
{
  "sources": ["git"],
  "output_format": "markdown"
}
EOF

echo "Setup complete!"
echo ""
echo "To test the tools:"
echo "  python3 tools/autonote.py tests/notes"
echo "  python3 tools/reportgen.py tools/config.json"
echo "  python3 tools/simple_datacleaner.py"
