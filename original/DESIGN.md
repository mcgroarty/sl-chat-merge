# Second Life Chat Log Merger

## Purpose

This utility merges and synchronizes Second Life chat log files across multiple workstations. It allows users to maintain complete, chronologically-sorted conversation history when using Second Life (or compatible viewers like Firestorm, Kokua) on different computers at different times.

## Problem Statement

Users who run Second Life on multiple workstations end up with fragmented chat logs - each machine only has the conversations that occurred while logged in from that specific computer. This utility solves that problem by combining chat logs bidirectionally between local installations and a central synchronized storage location (like Dropbox, Resilio Sync, or MEGA).

## How It Works

### Architecture

The tool consists of three bash scripts:

1. **`sl-chatmerge.sh`** - Main entry point that orchestrates bidirectional sync operations
2. **`sl-chatmerge-one.sh`** - Performs unidirectional merge from one directory to another
3. **`sl-chatsort.sh`** - Sorts and deduplicates chat log entries chronologically

### Processing Flow

#### Main Script (`sl-chatmerge.sh`)

- Detects the operating system (Windows via Cygwin, or macOS)
- Orchestrates bidirectional synchronization between:
  - Local Second Life viewer installations (SecondLife, Firestorm, Kokua)
  - Cloud-synced central storage directory
- Runs multiple sync passes in both directions to ensure consistency

#### Merge Script (`sl-chatmerge-one.sh`)

For each sync operation from source to destination:

1. **Validation**: Checks that both source and destination contain a `/logs` subdirectory. Aborts if either is missing (safety check to prevent accidental operation on wrong directories)

2. **Discovery**: Recursively scans both source and destination directories for `.txt` files (case-insensitive)

3. **Filtering**: Excludes system files and conflicts:
   - Any file path containing "conflicted copy" (case-insensitive)
   - Specific system files using regex pattern match at end of path:
     - `cef_log.txt` (Chromium Embedded Framework log)
     - `plugin_cookies.txt`
     - `search_history.txt`
     - `teleport_history.txt`
     - `typed_locations.txt`

4. **Directory Creation**: Creates all necessary subdirectories in the destination using `mkdir -p` (creates parent directories as needed, no error if already exists)

5. **File Processing**: For each chat log file:
   - If file exists only in source: copies it to destination
   - If file exists in both locations:
     - First checks if files are identical using `diff -q`
     - If different:
       - Concatenates both versions (source first, then destination)
       - Pipes combined content through `sl-chatsort.sh` to sort and deduplicate
       - Compares sorted result with current destination file
       - Updates destination only if sorted result differs from existing file
       - Reports "Updating [filename]..." when changes are made

6. **Optional Filtering**: Accepts command-line arguments (3rd parameter onward) to process only files matching specific patterns (case-insensitive grep on file paths)

#### Sort Script (`sl-chatsort.sh`)

Processes chat log entries through a pipeline:

1. **Line Ending Normalization**: Removes carriage returns (`\r`) to handle Windows line endings
2. **Multi-line Joining**: Uses AWK to join multi-line chat entries:
   - Lines starting with `[YYYY/MM/DD` (timestamp pattern) begin new entries
   - Lines NOT starting with timestamp are joined to the previous line
   - First line in file doesn't get a leading newline
3. **Chronological Sorting**: Sorts entries by characters 1-21 (the timestamp field `[YYYY/MM/DD HH:MM:SS]`)
4. **Deduplication**: Removes duplicate lines using `uniq`
5. **Environment**: Sets `LC_ALL='C'` for consistent locale-independent sorting

### Chat Log Format

Second Life chat logs use the format:

```text
[YYYY/MM/DD HH:MM:SS] Username: message text
```

Multi-line messages continue on subsequent lines without timestamps. The sort script intelligently handles these multi-line entries as atomic units.

**Important**: The timestamp format is exactly 20 characters: `[YYYY/MM/DD HH:MM:SS]` including the brackets. Sorting is performed on characters 1-21 of each line (timestamp plus the space after).

## Use Cases

1. **Workstation Switching**: User logs into SL from home computer on Monday, from work computer on Tuesday - both machines end up with complete chat history
2. **Backup and Recovery**: Central synchronized directory serves as backup of all conversations
3. **Multi-Viewer Support**: Supports multiple SL-compatible viewers (official client, Firestorm, Kokua)
4. **Cross-Platform**: Works on Windows (via Cygwin) and macOS

## Technical Details

### File System Operations

- **Temporary Files**: Uses three temp files in `/tmp/`:
  - `/tmp/sl-filelist.txt` - Combined list of all `.txt` files from both directories
  - `/tmp/sl-dirlist.txt` - Unique list of all subdirectories needed
  - `/tmp/sl-temp.txt` - Working file for merged and sorted content
- **Cleanup**: Removes all temp files after processing completes
- **Path Handling**: Strips source/destination base path from file list to create relative paths for comparison
- **Case Sensitivity**: Uses case-insensitive matching for `.txt` files and grep filters
- **Symbolic Links**: Follows symlinks during directory traversal (`find -L`)

### Safety and Validation

- **Directory Validation**: Requires `/logs` subdirectory in both source and destination (prevents accidental sync of wrong directories)
- **Diff-Based Updates**: Uses `diff -q` (quiet mode) to check if files differ before processing
- **Conservative Writes**: Only writes to destination when sorted result actually differs from existing content
- **Error Suppression**: Redirects stderr to `/dev/null` when reading files (`2>/dev/null`)

### Sorting and Locale

- **Locale Setting**: Sets `LC_ALL='C'` for byte-wise, locale-independent sorting
- **Sort Key**: Sorts on characters 1-21 of each line (the timestamp field)
- **Stability**: Consistent sorting behavior across different systems and locales

## Current Implementation

The current implementation uses bash scripts with standard Unix utilities:

- `find`, `grep`, `sed`, `awk`, `sort`, `uniq`, `diff`, `cut`, `wc`
- Designed for Cygwin (Windows) and native Unix/macOS environments
