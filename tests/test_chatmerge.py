"""
Tests for Second Life Chat Log Merger
"""

import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path to import sl-chatmerge
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util
spec = importlib.util.spec_from_file_location("sl_chatmerge", Path(__file__).parent.parent / "sl-chatmerge.py")
sl_chatmerge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl_chatmerge)


class TestPathHandling:
    """Test path expansion and validation."""
    
    def test_expand_path_with_tilde(self):
        """Test that ~ expands to home directory."""
        path = sl_chatmerge.expand_path("~/test")
        assert str(path) != "~/test"
        assert "test" in str(path)
        assert not str(path).startswith("~")
    
    def test_expand_path_absolute(self):
        """Test that absolute paths work."""
        path = sl_chatmerge.expand_path("/absolute/path")
        assert str(path) == "/absolute/path" or str(path) == "\\absolute\\path"
    
    def test_expand_path_with_spaces(self):
        """Test that paths with spaces are handled."""
        path = sl_chatmerge.expand_path("~/Library/Application Support")
        assert "Application Support" in str(path) or "Application" in str(path)


class TestFileExclusion:
    """Test file exclusion logic."""
    
    def test_exclude_conflicted_copy(self):
        """Test that conflicted copy files are excluded."""
        assert sl_chatmerge.should_exclude_file("logs/chat (conflicted copy).txt")
        assert sl_chatmerge.should_exclude_file("logs/Chat (Conflicted Copy).txt")
    
    def test_exclude_system_files(self):
        """Test that system files are excluded."""
        assert sl_chatmerge.should_exclude_file("logs/cef_log.txt")
        assert sl_chatmerge.should_exclude_file("logs/plugin_cookies.txt")
        assert sl_chatmerge.should_exclude_file("logs/search_history.txt")
        assert sl_chatmerge.should_exclude_file("logs/teleport_history.txt")
        assert sl_chatmerge.should_exclude_file("logs/typed_locations.txt")
    
    def test_include_regular_files(self):
        """Test that regular chat files are not excluded."""
        assert not sl_chatmerge.should_exclude_file("logs/Jane Doe.txt")
        assert not sl_chatmerge.should_exclude_file("logs/group/Meeting.txt")


class TestSortFunction:
    """Test the chat log sorting function."""
    
    def test_line_ending_normalization(self):
        """Test that CRLF is converted to LF."""
        content = "[2024/01/01 12:00:00] User: Hello\r\n[2024/01/01 12:01:00] User: World\r\n"
        result = sl_chatmerge.sort_chat_log(content, "test.txt")
        assert '\r' not in result
        assert result.count('\n') >= 2
    
    def test_empty_file(self):
        """Test that empty files get a newline."""
        result = sl_chatmerge.sort_chat_log("", "test.txt")
        assert result == '\n'
    
    def test_chronological_sorting(self):
        """Test that entries are sorted by timestamp."""
        content = """[2024/01/01 12:01:00] User: Second
[2024/01/01 12:00:00] User: First
[2024/01/01 12:02:00] User: Third
"""
        result = sl_chatmerge.sort_chat_log(content, "test.txt")
        lines = result.strip().split('\n')
        assert "First" in lines[0]
        assert "Second" in lines[1]
        assert "Third" in lines[2]
    
    def test_multi_line_entries(self):
        """Test that multi-line entries stay together."""
        content = """[2024/01/01 12:01:00] User: Second
This is line 2
This is line 3
[2024/01/01 12:00:00] User: First
Also multiline
"""
        result = sl_chatmerge.sort_chat_log(content, "test.txt")
        # First entry should come first and stay together
        assert result.index("First") < result.index("Second")
        assert result.index("Also multiline") < result.index("Second")
    
    def test_consecutive_deduplication(self):
        """Test that consecutive duplicates are removed."""
        content = """[2024/01/01 12:00:00] User: Hello
[2024/01/01 12:00:00] User: Hello
[2024/01/01 12:01:00] User: World
"""
        result = sl_chatmerge.sort_chat_log(content, "test.txt")
        # Should only have 2 entries
        assert result.count("[2024/01/01 12:00:00] User: Hello") == 1
        assert result.count("[2024/01/01 12:01:00] User: World") == 1
    
    def test_non_consecutive_duplicates_kept(self):
        """Test that non-consecutive duplicates are NOT removed."""
        content = """[2024/01/01 12:00:00] User: Hello
[2024/01/01 12:01:00] User: World
[2024/01/01 12:02:00] User: Hello
"""
        result = sl_chatmerge.sort_chat_log(content, "test.txt")
        # Should have both Hello entries
        assert result.count("Hello") == 2
    
    def test_trailing_newline(self):
        """Test that output ends with newline."""
        content = "[2024/01/01 12:00:00] User: Test"
        result = sl_chatmerge.sort_chat_log(content, "test.txt")
        assert result.endswith('\n')
    
    def test_malformed_timestamp_raises_error(self):
        """Test that malformed timestamps raise an error."""
        content = "[2024-01-01 12:00:00] User: Wrong format\n"
        with pytest.raises(ValueError) as exc_info:
            sl_chatmerge.sort_chat_log(content, "test.txt")
        assert "Malformed timestamp" in str(exc_info.value)
    
    def test_locale_independent_sorting(self):
        """Test that sorting is byte-wise, not locale-dependent."""
        content = """[2024/01/01 12:00:00] User: A
[2024/01/01 12:00:00] User: B
[2024/01/01 12:00:00] User: a
"""
        result = sl_chatmerge.sort_chat_log(content, "test.txt")
        lines = result.strip().split('\n')
        # Byte-wise sorting: uppercase comes before lowercase in ASCII
        assert lines[0].endswith(": A")
        assert lines[1].endswith(": B")
        assert lines[2].endswith(": a")


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_config_succeeds(self):
        """Test that valid config passes validation."""
        # Save original
        original = sl_chatmerge.DIRECTORIES
        try:
            sl_chatmerge.DIRECTORIES = [
                {"path": "/test", "mode": "rw"},
            ]
            config = sl_chatmerge.validate_config()
            assert len(config) == 1
        finally:
            sl_chatmerge.DIRECTORIES = original
    
    def test_validate_config_missing_mode(self):
        """Test that missing mode field is caught."""
        original = sl_chatmerge.DIRECTORIES
        try:
            sl_chatmerge.DIRECTORIES = [
                {"path": "/test"},
            ]
            with pytest.raises(SystemExit):
                sl_chatmerge.validate_config()
        finally:
            sl_chatmerge.DIRECTORIES = original
    
    def test_validate_config_invalid_mode(self):
        """Test that invalid mode value is caught."""
        original = sl_chatmerge.DIRECTORIES
        try:
            sl_chatmerge.DIRECTORIES = [
                {"path": "/test", "mode": "invalid"},
            ]
            with pytest.raises(SystemExit):
                sl_chatmerge.validate_config()
        finally:
            sl_chatmerge.DIRECTORIES = original


class TestIntegration:
    """Integration tests with temporary directories."""
    
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directory structure."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        
        (dir1 / "logs").mkdir(parents=True)
        (dir2 / "logs").mkdir(parents=True)
        
        return dir1, dir2
    
    def test_merge_simple_files(self, temp_dirs):
        """Test merging files from two directories."""
        dir1, dir2 = temp_dirs
        
        # Create file in dir1
        (dir1 / "logs" / "test.txt").write_text(
            "[2024/01/01 12:00:00] User: From dir1\n"
        )
        
        # Create file in dir2 with different content
        (dir2 / "logs" / "test.txt").write_text(
            "[2024/01/01 12:01:00] User: From dir2\n"
        )
        
        # Mock configuration
        original = sl_chatmerge.DIRECTORIES
        try:
            sl_chatmerge.DIRECTORIES = [
                {"path": str(dir1), "mode": "rw"},
                {"path": str(dir2), "mode": "rw"},
            ]
            
            # Get existing dirs
            config = sl_chatmerge.validate_config()
            existing_dirs = []
            for dir_config in config:
                exists, path = sl_chatmerge.check_directory_exists(dir_config)
                if exists and path:
                    existing_dirs.append((path, dir_config["mode"]))
            
            # Discover files
            all_files = sl_chatmerge.discover_files(existing_dirs, [])
            assert "logs/test.txt" in all_files
            
            # Merge
            sl_chatmerge.merge_and_sync_file("logs/test.txt", existing_dirs)
            
            # Check both files now have merged content
            content1 = (dir1 / "logs" / "test.txt").read_text()
            content2 = (dir2 / "logs" / "test.txt").read_text()
            
            assert content1 == content2
            assert "From dir1" in content1
            assert "From dir2" in content1
            
        finally:
            sl_chatmerge.DIRECTORIES = original
    
    def test_empty_file_handling(self, temp_dirs):
        """Test that empty files are handled correctly."""
        dir1, dir2 = temp_dirs
        
        # Create empty file in dir1
        (dir1 / "logs" / "empty.txt").write_text("")
        
        # Create file with content in dir2
        (dir2 / "logs" / "empty.txt").write_text(
            "[2024/01/01 12:00:00] User: Content\n"
        )
        
        # Mock configuration
        original = sl_chatmerge.DIRECTORIES
        try:
            sl_chatmerge.DIRECTORIES = [
                {"path": str(dir1), "mode": "rw"},
                {"path": str(dir2), "mode": "rw"},
            ]
            
            config = sl_chatmerge.validate_config()
            existing_dirs = []
            for dir_config in config:
                exists, path = sl_chatmerge.check_directory_exists(dir_config)
                if exists and path:
                    existing_dirs.append((path, dir_config["mode"]))
            
            sl_chatmerge.merge_and_sync_file("logs/empty.txt", existing_dirs)
            
            # Both should now have the content
            content1 = (dir1 / "logs" / "empty.txt").read_text()
            content2 = (dir2 / "logs" / "empty.txt").read_text()
            
            assert "Content" in content1
            assert "Content" in content2
            
        finally:
            sl_chatmerge.DIRECTORIES = original
