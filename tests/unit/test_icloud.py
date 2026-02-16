"""Unit tests for iCloud adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from macsetup.adapters.icloud import ICloudAdapter


class TestGetICloudDrivePath:
    """Tests for get_icloud_drive_path()."""

    def test_returns_correct_path(self):
        """get_icloud_drive_path() returns the standard iCloud Drive path."""
        adapter = ICloudAdapter()
        result = adapter.get_icloud_drive_path()
        expected = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        assert result == expected

    def test_returns_path_type(self):
        """get_icloud_drive_path() returns a Path object."""
        adapter = ICloudAdapter()
        result = adapter.get_icloud_drive_path()
        assert isinstance(result, Path)


class TestIsICloudAvailable:
    """Tests for is_icloud_available()."""

    def test_returns_true_when_dir_exists(self, tmp_path):
        """is_icloud_available() returns True when iCloud Drive directory exists."""
        icloud_dir = tmp_path / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        icloud_dir.mkdir(parents=True)

        adapter = ICloudAdapter()
        with patch.object(
            type(adapter),
            "get_icloud_drive_path",
            return_value=icloud_dir,
        ):
            with patch(
                "macsetup.adapters.icloud.ICLOUD_DRIVE_PATH",
                icloud_dir,
            ):
                result = adapter.is_icloud_available()
        assert result is True

    def test_returns_false_when_dir_absent(self, tmp_path):
        """is_icloud_available() returns False when iCloud Drive directory does not exist."""
        nonexistent = tmp_path / "Library" / "Mobile Documents" / "com~apple~CloudDocs"

        adapter = ICloudAdapter()
        with patch(
            "macsetup.adapters.icloud.ICLOUD_DRIVE_PATH",
            nonexistent,
        ):
            result = adapter.is_icloud_available()
        assert result is False

    def test_returns_false_when_path_is_file(self, tmp_path):
        """is_icloud_available() returns False when path exists but is a file, not a directory."""
        fake_file = tmp_path / "not_a_dir"
        fake_file.write_text("not a directory")

        adapter = ICloudAdapter()
        with patch(
            "macsetup.adapters.icloud.ICLOUD_DRIVE_PATH",
            fake_file,
        ):
            result = adapter.is_icloud_available()
        assert result is False

    def test_returns_false_when_symlink_to_nonexistent(self, tmp_path):
        """is_icloud_available() returns False when path is a symlink to nonexistent target."""
        broken_link = tmp_path / "broken_symlink"
        broken_link.symlink_to(tmp_path / "nonexistent_target")

        adapter = ICloudAdapter()
        with patch(
            "macsetup.adapters.icloud.ICLOUD_DRIVE_PATH",
            broken_link,
        ):
            result = adapter.is_icloud_available()
        assert result is False


class TestIsFileEvicted:
    """Tests for is_file_evicted() (T031)."""

    def test_returns_true_when_sf_dataless_flag_set(self, tmp_path):
        """is_file_evicted() returns True when SF_DATALESS flag is set."""
        adapter = ICloudAdapter()
        test_file = tmp_path / "evicted.yaml"
        test_file.write_text("content")

        SF_DATALESS = 0x40000000
        mock_stat = MagicMock()
        mock_stat.st_flags = SF_DATALESS
        mock_stat.st_blocks = 0
        mock_stat.st_size = 100

        with patch("os.stat", return_value=mock_stat):
            result = adapter.is_file_evicted(test_file)
        assert result is True

    def test_returns_false_for_local_files(self, tmp_path):
        """is_file_evicted() returns False for local (non-evicted) files."""
        adapter = ICloudAdapter()
        test_file = tmp_path / "local.yaml"
        test_file.write_text("content")

        result = adapter.is_file_evicted(test_file)
        assert result is False

    def test_fallback_heuristic_st_blocks_zero(self, tmp_path):
        """is_file_evicted() uses st_blocks==0, st_size>0 heuristic as fallback."""
        adapter = ICloudAdapter()
        test_file = tmp_path / "evicted.yaml"
        test_file.write_text("content")

        mock_stat = MagicMock()
        mock_stat.st_flags = 0
        mock_stat.st_blocks = 0
        mock_stat.st_size = 100

        with patch("os.stat", return_value=mock_stat):
            result = adapter.is_file_evicted(test_file)
        assert result is True


class TestFindConflictFiles:
    """Tests for find_conflict_files() (T032)."""

    def test_detects_conflict_pattern(self, tmp_path):
        """find_conflict_files() detects 'config 2.yaml' pattern."""
        adapter = ICloudAdapter()
        (tmp_path / "config.yaml").write_text("original")
        (tmp_path / "config 2.yaml").write_text("conflict")

        result = adapter.find_conflict_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "config 2.yaml"

    def test_detects_multiple_conflicts(self, tmp_path):
        """find_conflict_files() detects multiple conflict files."""
        adapter = ICloudAdapter()
        (tmp_path / "config.yaml").write_text("original")
        (tmp_path / "config 2.yaml").write_text("conflict 1")
        (tmp_path / "config 3.yaml").write_text("conflict 2")

        result = adapter.find_conflict_files(tmp_path)
        assert len(result) == 2

    def test_ignores_non_conflict_files(self, tmp_path):
        """find_conflict_files() ignores non-conflict files."""
        adapter = ICloudAdapter()
        (tmp_path / "config.yaml").write_text("original")
        (tmp_path / "other.yaml").write_text("not a conflict")
        (tmp_path / "readme.md").write_text("docs")

        result = adapter.find_conflict_files(tmp_path)
        assert len(result) == 0
