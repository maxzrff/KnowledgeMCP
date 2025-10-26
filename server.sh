#!/usr/bin/env bash
#
# MCP Knowledge Server - Server Management Script
# 
# Usage:
#   ./server.sh start   - Start the MCP server in background
#   ./server.sh stop    - Stop the MCP server
#   ./server.sh restart - Restart the MCP server
#   ./server.sh status  - Check server status
#   ./server.sh logs    - Show server logs (tail -f)
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON="$VENV_DIR/bin/python"
PID_FILE="$PROJECT_DIR/.mcp_server.pid"
LOG_FILE="$PROJECT_DIR/mcp_server.log"
SERVER_MODULE="src.mcp.server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found at: $VENV_DIR"
        log_info "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

# Check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is dead
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Get server PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# Start the server
start_server() {
    log_info "Starting MCP Knowledge Server..."
    
    check_venv
    
    if is_running; then
        log_warning "Server is already running (PID: $(get_pid))"
        return 0
    fi
    
    # Ensure data directories exist
    mkdir -p "$PROJECT_DIR/data/documents"
    mkdir -p "$PROJECT_DIR/data/chromadb"
    
    # Start server in background
    cd "$PROJECT_DIR"
    nohup "$PYTHON" -m "$SERVER_MODULE" > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    
    if is_running; then
        log_success "Server started successfully (PID: $pid)"
        log_info "Log file: $LOG_FILE"
        log_info "Use './server.sh logs' to view logs"
        log_info "Use './server.sh status' to check status"
    else
        log_error "Server failed to start. Check logs:"
        log_error "  tail -f $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Stop the server
stop_server() {
    log_info "Stopping MCP Knowledge Server..."
    
    if ! is_running; then
        log_warning "Server is not running"
        rm -f "$PID_FILE"
        return 0
    fi
    
    local pid=$(get_pid)
    log_info "Sending SIGTERM to process $pid..."
    kill "$pid"
    
    # Wait for graceful shutdown (max 10 seconds)
    local count=0
    while is_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if is_running; then
        log_warning "Server didn't stop gracefully, forcing..."
        kill -9 "$pid"
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    log_success "Server stopped"
}

# Restart the server
restart_server() {
    log_info "Restarting MCP Knowledge Server..."
    stop_server
    sleep 1
    start_server
}

# Show server status
show_status() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  MCP Knowledge Server - Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if is_running; then
        local pid=$(get_pid)
        log_success "Server is RUNNING"
        echo ""
        echo "  PID:        $pid"
        echo "  Log file:   $LOG_FILE"
        echo "  PID file:   $PID_FILE"
        echo ""
        
        # Show process info
        if command -v ps > /dev/null; then
            echo "  Process info:"
            ps -p "$pid" -o pid,ppid,user,%cpu,%mem,etime,command | tail -n +2 | sed 's/^/    /'
        fi
        
        echo ""
        echo "  Recent logs (last 10 lines):"
        echo "  ────────────────────────────────────────────────"
        if [ -f "$LOG_FILE" ]; then
            tail -n 10 "$LOG_FILE" | sed 's/^/    /'
        else
            echo "    (No log file found)"
        fi
    else
        log_warning "Server is NOT RUNNING"
        echo ""
        if [ -f "$LOG_FILE" ]; then
            echo "  Last logs:"
            echo "  ────────────────────────────────────────────────"
            tail -n 20 "$LOG_FILE" | sed 's/^/    /'
        fi
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Show logs (tail -f)
show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        log_error "Log file not found: $LOG_FILE"
        exit 1
    fi
    
    log_info "Showing logs (Ctrl+C to exit)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -f "$LOG_FILE"
}

# Show usage
show_usage() {
    cat << EOF
MCP Knowledge Server - Management Script

Usage:
  ./server.sh COMMAND

Commands:
  start       Start the MCP server in background
  stop        Stop the MCP server
  restart     Restart the MCP server
  status      Show server status and recent logs
  logs        Show live server logs (tail -f)
  help        Show this help message

Examples:
  ./server.sh start       # Start the server
  ./server.sh status      # Check if running
  ./server.sh logs        # Watch logs in real-time
  ./server.sh stop        # Stop the server

Files:
  PID file:   $PID_FILE
  Log file:   $LOG_FILE
  Virtual env: $VENV_DIR

For more information, see README.md
EOF
}

# Main script
main() {
    case "${1:-}" in
        start)
            start_server
            ;;
        stop)
            stop_server
            ;;
        restart)
            restart_server
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            if [ -z "${1:-}" ]; then
                log_error "No command specified"
            else
                log_error "Unknown command: $1"
            fi
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
