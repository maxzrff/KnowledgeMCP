#!/usr/bin/env bash
#
# Quick Start Script for MCP Knowledge Server
# This script helps you get started quickly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          MCP Knowledge Server - Quick Start                ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ Python 3 not found. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"
echo ""

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi
echo ""

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Download embedding model
echo -e "${BLUE}Checking embedding model...${NC}"
python3 << 'EOF'
try:
    from sentence_transformers import SentenceTransformer
    print("Loading model (this may take a moment on first run)...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("✓ Model ready")
except Exception as e:
    print(f"⚠ Error loading model: {e}")
    exit(1)
EOF
echo ""

# Run end-to-end demo
echo -e "${BLUE}Running end-to-end demo...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python tests/e2e_demo.py
echo ""

# Show next steps
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║                    Setup Complete! 🎉                      ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "  1. Start the MCP server:"
echo -e "     ${BLUE}./server.sh start${NC}"
echo ""
echo "  2. Check server status:"
echo -e "     ${BLUE}./server.sh status${NC}"
echo ""
echo "  3. View live logs:"
echo -e "     ${BLUE}./server.sh logs${NC}"
echo ""
echo "  4. Integrate with Claude Desktop:"
echo "     Edit your claude_desktop_config.json:"
echo -e "     ${BLUE}{"
echo "       \"mcpServers\": {"
echo "         \"knowledge\": {"
echo "           \"command\": \"python\","
echo "           \"args\": [\"-m\", \"src.mcp.server\"],"
echo "           \"cwd\": \"$SCRIPT_DIR\""
echo "         }"
echo "       }"
echo -e "     }${NC}"
echo ""
echo "  5. Read the documentation:"
echo -e "     ${BLUE}cat README.md${NC}"
echo -e "     ${BLUE}cat docs/SERVER_MANAGEMENT.md${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
