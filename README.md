# Second Life Chat Log Merger

Synchronize and merge Second Life chat logs across multiple workstations and viewers.

## ⚠️ Important Notice

This program is provided **as-is** and is intended for Second Life users, but is **not offered by Linden Lab**. It was written to address a personal need, and is not a comprehensive tool that may be appropriate for all users or all viewers.

**Before using this tool, you are strongly encouraged to make backups of your viewer logs.** While this tool has been designed with safety in mind, you should always have backups of important data.

If you encounter any issues or have questions, please file them at: <https://github.com/mcgroarty/sl-chat-merge/issues>

### Timestamp Requirements

**⚠️ Users are discouraged from using this tool if stable message ordering is required but seconds are not enabled in their viewer's chat timestamp settings.**

**Without seconds enabled:** Chat messages that occur within the same minute will not maintain chronological order. If preserving exact historical conversation flow is important to you, do not use this tool if seconds were not enabled in your viewer preferences.

## Overview

This tool maintains complete, chronologically-sorted conversation history when using Second Life on different computers or switching between viewers (Firestorm, Kokua, official client). It reads chat logs from all configured locations, merges them by timestamp, and writes the unified result back to all writable directories.

## Features

- **Multi-source merging**: Combines chat logs from all readable directories in a single pass
- **Bidirectional sync**: Keeps multiple viewer installations and cloud backup locations synchronized
- **Smart filtering**: Excludes system files and cloud sync conflicts automatically
- **Read-only protection**: Safely read from backup locations without modification
- **Dry-run mode**: Preview changes before executing
- **Cross-platform**: Works on Windows and macOS

## Usage

```bash
python sl-chatmerge.py [OPTIONS] [FILTERS...]
```

### Options

- `--help` - Display usage information and configuration format
- `--verbose`, `-v` - Enable detailed output showing all operations
- `--dry-run`, `-n` - Show what would be changed without modifying files

### Optional Filters

Provide pattern(s) as additional arguments to process only matching files:

```bash
python sl-chatmerge.py "Jane Doe"           # Only process Jane Doe's chat logs
python sl-chatmerge.py --dry-run "Group"    # Preview changes to group chat logs
```

## Configuration

Edit the directory configuration at the top of `sl-chatmerge.py`:

```python
DIRECTORIES = [
    {"path": "~/Library/Application Support/Firestorm/", "mode": "rw"},
    {"path": "~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/", "mode": "rw"},
    {"path": "~/Library/Application Support/SecondLife/", "mode": "rw"},
]
```

### Access Modes

- `r` - Read-only: Files are read but never modified
- `w` - Write-only: Files are written but not read as source
- `rw` - Read-write: Files are both read and written (bidirectional sync)

## How It Works

1. Validates that configured directories exist and contain a `/logs` subdirectory
2. Scans all readable (`r` or `rw`) directories for `.txt` chat log files
3. For each unique chat log file:
   - Reads all versions from readable directories
   - Merges and sorts by timestamp
   - Removes duplicate entries
   - Writes to all writable (`w` or `rw`) directories if content differs

## Requirements

- Python 3.8+
- No external dependencies

## Testing

```bash
pytest tests/
```

## License

See LICENSE file for details.
