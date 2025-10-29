# Second Life Chat Log Merger

## Purpose

This utility merges and synchronizes Second Life chat log files across multiple workstations. It allows users to maintain complete, chronologically-sorted conversation history when using Second Life (or compatible viewers like Firestorm, Kokua) on different computers at different times.

## Problem Statement

Users who run Second Life on multiple workstations end up with fragmented chat logs - each machine only has the conversations that occurred while logged in from that specific computer. This utility solves that problem by combining chat logs bidirectionally between local installations and a central synchronized storage location (like Dropbox, Resilio Sync, or MEGA).

## How It Works

### Architecture

The tool consists of three main functions:

1. **Main entry point** - Orchestrates bidirectional sync operations
2. **Merge function** - Performs unidirectional merge from one directory to another
3. **Sort function** - Sorts and deduplicates chat log entries chronologically

### Configuration

The implementation includes a directory configuration constant defined in the Python file that specifies:

- **Directory paths** to synchronize (must be absolute paths)
- **Access modes** for each directory:
  - `r` (read-only): Source directory - files are read but never modified; no directories created
  - `w` (write-only): Destination directory - files are written/updated but never read as source
  - `rw` (read-write): Bidirectional directory - acts as both source and destination

**Example configuration structure:**

```python
DIRECTORIES = [
    {"path": "~/Library/Application Support/Firestorm/", "mode": "rw"},
    {"path": "~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/", "mode": "rw"},
    {"path": "~/Library/Application Support/SecondLife/", "mode": "rw"},
]
```

**Path Requirements**:
- Paths should be absolute or use `~` for home directory
- `~` is expanded to the user's home directory (works on Windows, macOS, and Linux)
- Always use forward slash (`/`) as directory separator, even on Windows
- Paths support space characters in file and directory names
- No other environment variable expansion is supported
- Relative paths are not supported

**Validation**: The program terminates with an error if any directory entry is missing the `mode` field.

### Command-Line Interface

The tool supports the following command-line options:

- **`--help`**: Displays usage information, configuration format, and available options
- **`--verbose`** or **`-v`**: Enables verbose output with additional information about:
  - Files being scanned
  - Comparison results
  - Processing details
  - Sync operations performed
- **`--dry-run`** or **`-n`**: Simulation mode that:
  - Shows what files would be written or updated
  - Shows what directories would be created
  - Never actually writes files or creates directories
  - Useful for previewing sync operations before executing them

Additional filtering can be provided as positional arguments to process only files matching specific patterns (case-insensitive substring match on file paths).

### Processing Flow

#### Main Entry Point

- Loads and validates the directory configuration constant
- Checks that all directory entries have a valid access mode (`r`, `w`, or `rw`)
- Validates which configured directories actually exist on the file system
- For each unique chat log file found across all directories:
  1. Reads the file from all existing directories with `r` or `rw` access
  2. Merges all versions in memory using the sort function
  3. Writes the merged result to all existing directories with `w` or `rw` access
- This approach is more efficient than pairwise merging: each file is read once from all sources, merged once, then written once to all destinations

#### Merge Function

For each unique chat log file across all configured directories:

1. **Validation**: Checks that all directories contain a `/logs` subdirectory. Skips directories that don't exist or lack this subdirectory

2. **Discovery**: Recursively scans all existing directories with `r` or `rw` access for `.txt` files
   - File extension matching is case-insensitive (matches `.txt`, `.TXT`, `.Txt`, etc.)
   - Builds a union of all unique file paths found across all readable directories
   - Once discovered, file paths are used exactly as found on the file system

3. **Filtering**: Excludes system files and conflicts:
   - Any file path containing "conflicted copy" (case-insensitive)
   - Specific system files matched at end of path:
     - `cef_log.txt` (Chromium Embedded Framework log)
     - `plugin_cookies.txt`
     - `search_history.txt`
     - `teleport_history.txt`
     - `typed_locations.txt`

4. **Directory Creation**: Creates all necessary subdirectories in writable destinations (creates parent directories as needed, no error if already exists)
   - Only applies to existing directories with `w` or `rw` access mode
   - Read-only (`r`) directories are never modified - no subdirectories are created
   - In dry-run mode, reports directories that would be created without actually creating them

5. **File Processing**: For each unique chat log file:
   - Reads all versions of the file from directories where it exists (only from `r` or `rw` directories)
   - Empty files are treated as having no chat content to merge
   - Concatenates all versions in memory (in order of directory configuration)
   - Passes combined content through the sort function to sort and deduplicate
   - **Malformed Timestamp Handling**: If any file contains lines with malformed timestamps, stops immediately with a verbose error message and makes no changes (may indicate a new system file needing exclusion)
   - For each existing directory with `w` or `rw` access:
     - If file doesn't exist: writes the merged file (or reports in dry-run mode)
     - If file exists (including empty files): compares with merged result
       - Updates only if merged result differs (or reports in dry-run mode)
       - Reports "Updating [filename]..." when changes are made (or "Would update [filename]..." in dry-run mode)
       - Reports "Adding [filename]..." when creating new files (or "Would add [filename]..." in dry-run mode)

6. **Optional Filtering**: Accepts command-line arguments to process only files matching specific patterns (case-insensitive substring match on file paths)

#### Sort Function

Processes chat log entries:

1. **Line Ending Normalization**: Converts all line endings to Unix style (LF)
   - Removes carriage returns to handle Windows line endings (CRLF → LF)
   - Ensures consistent line endings regardless of source platform
2. **Multi-line Joining**: Joins multi-line chat entries:
   - Lines starting with `[YYYY/MM/DD` (timestamp pattern) begin new entries
   - Lines NOT starting with timestamp are joined to the previous line
   - First line in file doesn't get a leading newline
3. **Timestamp Validation**: Checks that all lines starting with `[` have valid timestamps
   - If malformed timestamps are detected, raises an error and stops processing
4. **Chronological Sorting**: Sorts entries by the timestamp field (characters 1-21: `[YYYY/MM/DD HH:MM:SS]` plus space)
5. **Deduplication**: Removes consecutive duplicate lines (like Unix `uniq`)
   - Only removes duplicates that appear immediately after each other in the sorted output
   - Does not remove duplicates that appear elsewhere in the file
6. **Trailing Newline**: Ensures output ends with a newline character
7. **Locale Independence**: Uses byte-wise comparison for consistent sorting across different systems

### Chat Log Format

Second Life chat logs use the format:

```text
[YYYY/MM/DD HH:MM:SS] Username: message text
```

Multi-line messages continue on subsequent lines without timestamps. The sort function intelligently handles these multi-line entries as atomic units.

**Important**: The timestamp format is exactly 20 characters: `[YYYY/MM/DD HH:MM:SS]` including the brackets. Sorting is performed on characters 1-21 of each line (timestamp plus the space after).

**Line Endings**: All output files use Unix-style line endings (LF only, `\n`). Files with Windows line endings (CRLF, `\r\n`) are automatically converted during processing.

## Use Cases

1. **Workstation Switching**: User logs into SL from home computer on Monday, from work computer on Tuesday - both machines end up with complete chat history
2. **Backup and Recovery**: Central synchronized directory serves as backup of all conversations
3. **Multi-Viewer Support**: Supports multiple SL-compatible viewers (official client, Firestorm, Kokua)
4. **Cross-Platform**: Works on Windows and macOS (all files use Unix line endings)

## Technical Details

### File System Operations

- **In-Memory Processing**: All file lists, directory structures, and merged content are processed in memory
  - No temporary files are created or used
  - File lists and merge operations are held in memory during processing
- **Path Handling**:
  - Paths can be absolute or use `~` for home directory (expanded to user's home directory on all platforms)
  - Always use forward slash (`/`) as directory separator (works on all platforms including Windows)
  - Supports space characters in file and directory names
  - No other environment variable expansion supported
  - Relative paths are not supported
  - Strips base path from file list to create relative paths for comparison
- **Line Endings**: Always writes Unix-style line endings (LF, `\n`) regardless of source file format
- **Case Sensitivity**: Uses case-insensitive matching for `.txt` files and pattern filters
- **Symbolic Links**: Follows symbolic links during directory traversal

### Safety and Validation

- **Directory Validation**: Requires `/logs` subdirectory in directories before processing (prevents accidental sync of wrong directories)
- **Existence Check**: Only processes directories that actually exist on the file system
- **Read-Only Protection**: Directories with `r` access mode are never modified - no files written, no directories created
- **Malformed Timestamp Detection**: Stops immediately with verbose error if malformed timestamps are detected (may indicate new system files)
- **Dry-Run Mode**: When enabled, performs all analysis and reports actions without making any file system modifications
- **Change Detection**: Checks if files differ before writing
- **Conservative Writes**: Only writes to destination when merged result actually differs from existing content
- **Error Handling**: Gracefully handles missing directories and files that may not exist

### Sorting Behavior

- **Locale Independence**: Uses byte-wise comparison for consistent sorting across different systems and locales
- **Sort Key**: Sorts on characters 1-21 of each line (the timestamp field)
- **Deduplication**: Removes only consecutive duplicate lines after sorting (equivalent to Unix `uniq`)
- **Stability**: Consistent sorting behavior regardless of system locale settings

## Implementation Requirements

### Python Specifications

- **Type Safety**: Full type hints for all functions, parameters, and return values
- **Testing Framework**: pytest for all unit and integration tests
- **Test Organization**: Tests located in a `tests/` directory
- **Command-Line Interface**: Argument parsing for `--help`, `--verbose`/`-v`, and `--dry-run`/`-n` options
- **Configuration**: Directory configuration defined as a constant (`DIRECTORIES`) in the main Python file
- **Path Expansion**: Implements `~` expansion for home directory on all platforms (Windows, macOS, Linux)
- **Path Separators**: Uses forward slash (`/`) as directory separator on all platforms, including Windows
- **Test Coverage**: Comprehensive test coverage for:
  - Sort function (line endings, multi-line entries, timestamp parsing, timestamp validation, consecutive deduplication)
  - Merge function (file discovery, filtering, directory creation, file comparison, multi-source merging, empty files)
  - Main entry point (directory existence checking, read-all-then-write-all logic, dry-run mode, verbose output)
  - Edge cases (empty files, malformed timestamps, missing directories, special characters, non-existent directories, paths with spaces)
  - Command-line option handling
  - Line ending conversion (CRLF to LF)
  - Path handling (tilde expansion, forward slash separators on all platforms)

