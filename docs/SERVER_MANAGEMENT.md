# Server Management Scripts

This directory contains scripts for managing the MCP Knowledge Server.

## server.sh - Server Management Script

A comprehensive bash script for managing the MCP server lifecycle.

### Usage

```bash
./server.sh COMMAND
```

### Commands

| Command   | Description                           |
|-----------|---------------------------------------|
| `start`   | Start the MCP server in background    |
| `stop`    | Stop the MCP server gracefully        |
| `restart` | Restart the MCP server                |
| `status`  | Show server status and recent logs    |
| `logs`    | Show live server logs (tail -f)       |
| `help`    | Display help message                  |

### Examples

```bash
# Start the server
./server.sh start

# Check if running
./server.sh status

# Watch logs in real-time
./server.sh logs

# Stop the server
./server.sh stop

# Restart after configuration changes
./server.sh restart
```

### Features

- ✅ **Background execution**: Server runs as daemon
- ✅ **PID tracking**: Stores process ID in `.mcp_server.pid`
- ✅ **Log management**: All output goes to `mcp_server.log`
- ✅ **Status checking**: Shows if server is running with process info
- ✅ **Graceful shutdown**: SIGTERM with fallback to SIGKILL
- ✅ **Error handling**: Checks virtual environment and dependencies
- ✅ **Colored output**: Clear visual feedback

### Files Created

- `.mcp_server.pid` - Process ID file
- `mcp_server.log` - Server log file

### Requirements

- Bash shell
- Python virtual environment at `./venv`
- Installed dependencies (`pip install -r requirements.txt`)

## Troubleshooting

### Server won't start

```bash
# Check logs
./server.sh status
tail -f mcp_server.log

# Verify virtual environment
source venv/bin/activate
python -m src.mcp.server  # Run in foreground

# Check dependencies
pip install -r requirements.txt
```

### Permission issues

```bash
# Make sure script is executable
chmod +x server.sh

# Check data directory permissions
ls -la data/
chmod -R u+rw data/
```

### Process doesn't stop

```bash
# Force kill if needed
./server.sh stop
# Or manually:
kill -9 $(cat .mcp_server.pid)
```

## Development

When developing, run the server in foreground mode:

```bash
# Activate virtual environment
source venv/bin/activate

# Run in foreground with debug logging
KNOWLEDGE_LOG_LEVEL=DEBUG python -m src.mcp.server
```

## Support

For issues with server management:
1. Check logs: `./server.sh logs` or `tail -f mcp_server.log`
2. Check status: `./server.sh status`
3. Review configuration: `cat src/config/default_config.yaml`
4. See main README.md for general troubleshooting
