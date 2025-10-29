#!/usr/bin/env python3
"""
Second Life Chat Log Merger

Synchronizes and merges Second Life chat logs across multiple workstations and viewers.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


# Configuration: Directory paths and access modes
DIRECTORIES = [
    {"path": "~/AppData/Roaming/Firestorm_x64/", "mode": "rw"},
    {"path": "~/AppData/Roaming/Kokua/", "mode": "rw"},
    {"path": "~/AppData/Roaming/SecondLife/", "mode": "rw"},
    {"path": "~/Library/Application Support/Firestorm/", "mode": "rw"},
    {"path": "~/Library/Application Support/Kokua/", "mode": "rw"},
    {"path": "~/Library/Application Support/SecondLife/", "mode": "rw"},
    {"path": "~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/", "mode": "rw"},
]

# System files to exclude (matched at end of path)
EXCLUDED_FILES = [
    "avatar_icons_cache.txt",
    "cef_log.txt",
    "plugin_cookies.txt",
    "render_mute_settings.txt"
    "search_history.txt",
    "teleport_history.txt",
    "typed_locations.txt",
]

# Directories to exclude (matched at start of relative path)
EXCLUDED_DIRECTORIES = [
    "logs/",
    "user_settings/",
]

# Global flags
VERBOSE = False
DRY_RUN = False
FORCE = False


def log_verbose(message: str) -> None:
    """Print message if verbose mode is enabled."""
    if VERBOSE:
        print(f"[VERBOSE] {message}")


def log_info(message: str) -> None:
    """Print informational message."""
    print(message)


def log_error(message: str) -> None:
    """Print error message to stderr."""
    print(f"ERROR: {message}", file=sys.stderr)


def expand_path(path: str) -> Path:
    """
    Expand path with ~ substitution and ensure forward slashes.
    
    Args:
        path: Path string, possibly with ~
        
    Returns:
        Path object with expanded home directory
    """
    # Expand ~ to home directory
    expanded = os.path.expanduser(path)
    # Convert to Path which handles forward slashes on all platforms
    return Path(expanded)


def validate_config() -> List[Dict[str, str]]:
    """
    Validate the DIRECTORIES configuration.
    
    Returns:
        Validated list of directory configurations
        
    Raises:
        SystemExit: If configuration is invalid
    """
    if not DIRECTORIES:
        log_error("No directories configured in DIRECTORIES constant")
        sys.exit(1)
    
    for idx, dir_config in enumerate(DIRECTORIES):
        if "mode" not in dir_config:
            log_error(f"Directory entry {idx} is missing 'mode' field")
            sys.exit(1)
        
        if dir_config["mode"] not in ("r", "w", "rw"):
            log_error(f"Directory entry {idx} has invalid mode '{dir_config['mode']}' (must be 'r', 'w', or 'rw')")
            sys.exit(1)
        
        if "path" not in dir_config:
            log_error(f"Directory entry {idx} is missing 'path' field")
            sys.exit(1)
    
    return DIRECTORIES


def check_directory_exists(dir_config: Dict[str, str]) -> Tuple[bool, Optional[Path]]:
    """
    Check if a directory exists and contains /logs subdirectory.
    
    Args:
        dir_config: Dictionary with 'path' and 'mode'
        
    Returns:
        Tuple of (exists, expanded_path or None)
    """
    path = expand_path(dir_config["path"])
    logs_path = path / "logs"
    
    if not path.exists():
        log_verbose(f"Directory does not exist: {path}")
        return False, None
    
    if not logs_path.exists() or not logs_path.is_dir():
        log_verbose(f"Directory missing /logs subdirectory: {path}")
        return False, None
    
    log_verbose(f"Directory validated: {path}")
    return True, path


def should_exclude_file(relative_path: str) -> bool:
    """
    Check if a file should be excluded based on path patterns.
    
    Args:
        relative_path: Relative path from base directory
        
    Returns:
        True if file should be excluded
    """
    # Exclude files with "conflicted copy" in path (case-insensitive)
    if "conflicted copy" in relative_path.lower():
        return True
    
    # Exclude specific system files (matched at end of path, case-insensitive)
    relative_path_lower = relative_path.lower()
    for excluded in EXCLUDED_FILES:
        if relative_path_lower.endswith("/" + excluded.lower()):
            return True
    
    return False


def discover_files(directories: List[Tuple[Path, str]], filters: List[str]) -> Set[str]:
    """
    Discover all .txt files across readable directories.
    
    Scans user-specific subdirectories (e.g., UserName/*.txt) but excludes
    certain directories like logs/ and user_settings/.
    
    Args:
        directories: List of (path, mode) tuples for existing directories
        filters: Optional substring filters for file paths
        
    Returns:
        Set of relative file paths (relative to each directory root)
    """
    all_files: Set[str] = set()
    
    for dir_path, mode in directories:
        # Only scan readable directories
        if mode not in ("r", "rw"):
            continue
        
        log_verbose(f"Scanning directory: {dir_path}")
        
        # Recursively find all .txt files in the base directory
        for txt_file in dir_path.rglob("*.txt"):
            # Get relative path from the directory root
            try:
                relative = txt_file.relative_to(dir_path)
                relative_str = str(relative).replace(os.sep, "/")  # Ensure forward slashes
                
                # Exclude files in excluded directories (case-insensitive)
                relative_str_lower = relative_str.lower()
                if any(relative_str_lower.startswith(excluded_dir.lower()) for excluded_dir in EXCLUDED_DIRECTORIES):
                    log_verbose(f"Excluding (in excluded directory): {relative_str}")
                    continue
                
                # Apply exclusion filters
                if should_exclude_file(relative_str):
                    log_verbose(f"Excluding: {relative_str}")
                    continue
                
                # Apply user filters if provided
                if filters:
                    if not any(f.lower() in relative_str.lower() for f in filters):
                        continue
                
                all_files.add(relative_str)
                log_verbose(f"Found: {relative_str}")
            except ValueError:
                # File is not relative to dir_path, skip
                continue
    
    log_info(f"Discovered {len(all_files)} unique chat log files")
    return all_files


def sort_chat_log(content: str, file_path: str) -> str:
    """
    Sort and deduplicate chat log entries chronologically.
    
    Args:
        content: Raw chat log content
        file_path: Path for error reporting
        
    Returns:
        Sorted and deduplicated content with Unix line endings
        
    Raises:
        ValueError: If malformed timestamps are detected
    """
    # Step 1: Normalize line endings (CRLF -> LF)
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    if not content:
        return '\n'  # Empty file gets single newline
    
    lines = content.split('\n')
    
    # Step 2: Join multi-line entries
    # Pattern for timestamp: [YYYY/MM/DD HH:MM:SS] or [YYYY/MM/DD HH:MM] or [YYYY/MM/DD HH:MM AM/PM]
    # Standard format: 20 chars (with seconds), Short format: 17-19 chars (without seconds)
    # 12-hour format: 20-22 chars (with AM/PM)
    # Hours and minutes can be 1-2 digits
    timestamp_pattern = re.compile(r'^\[\d{4}/\d{2}/\d{2} \d{1,2}:\d{1,2}(:\d{2})?( [AP]M)?\]')
    
    entries: List[str] = []
    current_entry: List[str] = []
    
    for line in lines:
        if timestamp_pattern.match(line):
            # Start of new entry
            if current_entry:
                entries.append('\n'.join(current_entry))
            current_entry = [line]
        elif line:  # Non-empty continuation line
            # Continuation of current entry (including lines with just whitespace)
            if current_entry:
                current_entry.append(line)
            else:  # First line without timestamp
                current_entry = [line]
    
    # Add last entry
    if current_entry:
        entries.append('\n'.join(current_entry))
    
    # Step 3: Validate and normalize timestamps
    # Pattern to extract timestamp components for normalization (including optional AM/PM)
    timestamp_parse = re.compile(
        r'^\[(\d{4})/(\d{2})/(\d{2}) (\d{1,2}):(\d{1,2})(?::(\d{2}))?( [AP]M)?\]'
    )
    
    normalized_entries: List[str] = []
    for entry in entries:
        lines_in_entry = entry.split('\n')
        first_line = lines_in_entry[0]
        
        if first_line.startswith('['):
            match = timestamp_parse.match(first_line)
            if not match:
                raise ValueError(
                    f"Malformed timestamp in {file_path}:\n"
                    f"  Line: {first_line[:80]}\n"
                    f"  Expected format: [YYYY/MM/DD HH:MM:SS] or [YYYY/MM/DD HH:MM] or [YYYY/MM/DD HH:MM AM/PM]"
                )
            
            # Normalize timestamp: pad hours and minutes to 2 digits, convert AM/PM to 24-hour
            year, month, day, hour, minute, second, ampm = match.groups()
            hour = int(hour)
            minute = int(minute)
            
            # Convert 12-hour format to 24-hour format
            if ampm:
                ampm = ampm.strip()  # Remove leading space
                if ampm == 'AM':
                    if hour == 12:
                        hour = 0  # 12 AM is 00:00
                elif ampm == 'PM':
                    if hour != 12:
                        hour += 12  # 1-11 PM becomes 13-23
                    # 12 PM stays as 12
            
            # Format with leading zeros
            hour_str = str(hour).zfill(2)
            minute_str = str(minute).zfill(2)
            
            # Reconstruct timestamp (always in 24-hour format, no AM/PM in output)
            if second:
                normalized_ts = f"[{year}/{month}/{day} {hour_str}:{minute_str}:{second}]"
            else:
                normalized_ts = f"[{year}/{month}/{day} {hour_str}:{minute_str}]"
            
            # Replace first line with normalized timestamp
            remainder = first_line[match.end():]  # Everything after the timestamp
            lines_in_entry[0] = normalized_ts + remainder
            normalized_entries.append('\n'.join(lines_in_entry))
        else:
            # Entry doesn't start with timestamp (shouldn't happen, but preserve it)
            normalized_entries.append(entry)
    
    # Step 4: Sort by timestamp, then by full entry content for stability
    # Use UTF-8 encoding to properly handle Unicode characters
    # Timestamps are now normalized, so all have consistent format
    def sort_key(entry: str) -> bytes:
        # Sort by full entry to ensure stable, deterministic ordering
        # This ensures identical entries sort together for deduplication
        # Use UTF-8 to preserve Unicode characters that may appear at end of entries
        return entry.encode('utf-8')
    
    sorted_entries = sorted(normalized_entries, key=sort_key)
    
    # Step 5: Remove consecutive duplicates
    deduplicated: List[str] = []
    prev_entry = None
    for entry in sorted_entries:
        if entry != prev_entry:
            deduplicated.append(entry)
            prev_entry = entry
    
    # Step 6: Join with newlines and ensure trailing newline
    result = '\n'.join(deduplicated)
    if result and not result.endswith('\n'):
        result += '\n'
    
    return result


def read_file_content(file_path: Path) -> str:
    """
    Read file content, handling encoding issues.
    
    Args:
        file_path: Path to file
        
    Returns:
        File content as string
    """
    try:
        return file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Try latin-1 as fallback
        log_verbose(f"UTF-8 decode failed, trying latin-1: {file_path}")
        return file_path.read_text(encoding='latin-1')


def merge_and_sync_file(
    relative_path: str,
    directories: List[Tuple[Path, str]]
) -> None:
    """
    Merge a single file across all directories.
    
    Args:
        relative_path: Relative path from directory root
        directories: List of (path, mode) tuples
    """
    log_verbose(f"Processing: {relative_path}")
    
    # Step -1: Skip excluded directories (case-insensitive)
    relative_path_lower = relative_path.lower()
    if any(relative_path_lower.startswith(excluded_dir.lower()) for excluded_dir in EXCLUDED_DIRECTORIES):
        log_verbose(f"  Skipping excluded directory: {relative_path}")
        return
    
    # Step 0: Quick optimization - check if all versions have identical file sizes across ALL directories
    # If so, they're likely identical and we can skip processing (unless --force is used)
    # This check includes both readable AND writable directories to ensure we don't skip writing missing files
    if not FORCE:
        file_sizes: Set[int] = set()
        file_paths_for_size_check: List[Path] = []
        all_dirs_have_file = True
        
        for dir_path, mode in directories:
            file_path = dir_path / relative_path
            if file_path.exists():
                file_sizes.add(file_path.stat().st_size)
                file_paths_for_size_check.append(file_path)
            else:
                # If any directory is missing the file, we can't skip
                all_dirs_have_file = False
        
        # Only skip if:
        # 1. All directories have the file (no missing files to write)
        # 2. All existing files have identical size
        # 3. At least one file exists
        if all_dirs_have_file and len(file_sizes) == 1 and len(file_paths_for_size_check) > 0:
            log_verbose(f"  All versions have identical size ({file_sizes.pop()} bytes), skipping merge")
            return
    
    # Step 1: Read all versions from readable directories
    contents: List[str] = []
    readable_found = False
    
    for dir_path, mode in directories:
        if mode not in ("r", "rw"):
            continue
        
        file_path = dir_path / relative_path
        if file_path.exists():
            readable_found = True
            content = read_file_content(file_path)
            contents.append(content)
            log_verbose(f"  Read from {dir_path}: {len(content)} bytes")
    
    if not readable_found:
        log_verbose(f"  File not found in any readable directory")
        return
    
    # Step 2: Merge all contents
    combined = ''.join(contents)
    
    # Step 3: Sort and deduplicate
    try:
        merged = sort_chat_log(combined, relative_path)
    except ValueError as e:
        log_error(str(e))
        log_error("Stopping processing to avoid data corruption.")
        sys.exit(1)
    
    # Step 4: Write to all writable directories
    for dir_path, mode in directories:
        if mode not in ("w", "rw"):
            continue
        
        file_path = dir_path / relative_path
        
        # Ensure parent directory exists
        parent_dir = file_path.parent
        if not parent_dir.exists():
            if DRY_RUN:
                log_info(f"Would create directory: {parent_dir}")
            else:
                parent_dir.mkdir(parents=True, exist_ok=True)
                log_verbose(f"Created directory: {parent_dir}")
        
        # Check if we need to write by comparing content
        needs_write = False
        action = "Adding"
        
        if file_path.exists():
            # Read existing file and compare with merged content
            existing = read_file_content(file_path)
            if existing != merged:
                needs_write = True
                action = "Updating"
            else:
                # File content is identical, no write needed
                log_verbose(f"  Skipping {dir_path.name} (content unchanged)")
        else:
            needs_write = True
            action = "Adding"
        
        if needs_write:
            if DRY_RUN:
                log_info(f"Would {action.lower()}: {relative_path} in {dir_path.name}")
            else:
                file_path.write_text(merged, encoding='utf-8')
                log_info(f"{action} {relative_path}...")
        else:
            # In dry-run mode, still report that file is unchanged
            if DRY_RUN and file_path.exists():
                log_verbose(f"  Would skip {dir_path.name} (content unchanged)")


def main() -> None:
    """Main entry point."""
    global VERBOSE, DRY_RUN, FORCE
    
    parser = argparse.ArgumentParser(
        description="Merge and synchronize Second Life chat logs across multiple directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run sync with default directories
  %(prog)s --dry-run          # Preview what would change
  %(prog)s --verbose          # Show detailed output
  %(prog)s --force            # Force processing even if files appear identical
  %(prog)s "Jane Doe"         # Only process Jane Doe's chat logs
  %(prog)s --dry-run "Group"  # Preview changes to group chats

Configuration:
  Edit the DIRECTORIES constant at the top of this script.
  Use 'r' for read-only, 'w' for write-only, 'rw' for read-write.
"""
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output showing all operations'
    )
    
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force processing all files, even if they appear identical by size'
    )
    
    parser.add_argument(
        'filters',
        nargs='*',
        help='Optional filename patterns to filter which files to process'
    )
    
    args = parser.parse_args()
    
    VERBOSE = args.verbose
    DRY_RUN = args.dry_run
    FORCE = args.force
    
    if DRY_RUN:
        log_info("=== DRY RUN MODE - No changes will be made ===")
    
    # Validate configuration
    config = validate_config()
    
    # Check which directories exist
    existing_dirs: List[Tuple[Path, str]] = []
    for dir_config in config:
        exists, path = check_directory_exists(dir_config)
        if exists and path:
            existing_dirs.append((path, dir_config["mode"]))
            log_verbose(f"Using directory: {path} (mode: {dir_config['mode']})")
    
    if not existing_dirs:
        log_error("No configured directories found on this system")
        sys.exit(1)
    
    # Check that we have at least one readable and one writable
    has_readable = any(mode in ("r", "rw") for _, mode in existing_dirs)
    has_writable = any(mode in ("w", "rw") for _, mode in existing_dirs)
    
    if not has_readable:
        log_error("No readable directories (r or rw) found")
        sys.exit(1)
    
    if not has_writable:
        log_error("No writable directories (w or rw) found")
        sys.exit(1)
    
    # Discover all files
    all_files = discover_files(existing_dirs, args.filters)
    
    if not all_files:
        log_info("No chat log files found to process")
        return
    
    # Group files by user directory for progress reporting
    from collections import defaultdict
    files_by_user: defaultdict = defaultdict(list)
    for relative_path in sorted(all_files):
        # Extract user directory (first component of path)
        parts = relative_path.split('/')
        if parts:
            user_dir = parts[0]
            files_by_user[user_dir].append(relative_path)
    
    # Process each file, grouped by user directory
    log_info(f"Processing {len(all_files)} files across {len(files_by_user)} user directories...")
    
    for user_dir in sorted(files_by_user.keys()):
        user_files = files_by_user[user_dir]
        log_info(f"  {user_dir}: {len(user_files)} file(s)")
        
        for relative_path in user_files:
            merge_and_sync_file(relative_path, existing_dirs)
    
    if DRY_RUN:
        log_info("=== DRY RUN COMPLETE - No actual changes were made ===")
    else:
        log_info("Sync complete!")


if __name__ == "__main__":
    main()
