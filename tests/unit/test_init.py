"""Unit tests for init service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from macsetup.services.init import InitService


class TestInitServiceInitICloudFresh:
    """Tests for InitService.init_icloud() fresh case (US1 - T010)."""

    def test_creates_icloud_macsetup_dir(self, tmp_path):
        """init_icloud() creates the macsetup dir inside iCloud Drive."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()
        icloud_macsetup = icloud_drive / "macsetup"

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        service = InitService(
            icloud_adapter=mock_adapter,
            default_config_dir=default_dir,
        )
        result = service.init_icloud()

        assert icloud_macsetup.is_dir()
        assert result["success"] is True
        assert result["storage"] == "icloud"

    def test_writes_pointer_file(self, tmp_path):
        """init_icloud() writes a pointer file pointing to the iCloud macsetup dir."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        service = InitService(
            icloud_adapter=mock_adapter,
            default_config_dir=default_dir,
        )
        service.init_icloud()

        pointer_path = default_dir / "config-dir"
        assert pointer_path.exists()
        assert pointer_path.read_text().strip() == str(icloud_drive / "macsetup")

    def test_errors_when_icloud_unavailable(self, tmp_path):
        """init_icloud() returns error when iCloud Drive is not available."""
        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = False

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        service = InitService(
            icloud_adapter=mock_adapter,
            default_config_dir=default_dir,
        )
        result = service.init_icloud()

        assert result["success"] is False
        assert (
            "not available" in result["error"].lower()
            or "not available" in result.get("message", "").lower()
        )


class TestInitServiceStatus:
    """Tests for InitService.status() (US1 - T011)."""

    def test_returns_local_when_no_pointer(self, tmp_path):
        """status() returns 'local' when no pointer file exists."""
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = False

        service = InitService(
            icloud_adapter=mock_adapter,
            default_config_dir=default_dir,
        )
        result = service.status()

        assert result["storage"] == "local"

    def test_returns_icloud_with_path_when_pointer_exists(self, tmp_path):
        """status() returns 'icloud' with path when pointer file exists."""
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer_file = default_dir / "config-dir"
        pointer_file.write_text(str(icloud_dir))

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True

        service = InitService(
            icloud_adapter=mock_adapter,
            default_config_dir=default_dir,
        )
        result = service.status()

        assert result["storage"] == "icloud"
        assert result["config_dir"] == str(icloud_dir)
        assert result["pointer_file"] == str(pointer_file)


class TestInitServiceMigration:
    """Tests for InitService.init_icloud() migration case (US2 - T018)."""

    def _setup_local_config(self, default_dir: Path) -> None:
        """Create a local config with config.yaml and dotfiles."""
        default_dir.mkdir(exist_ok=True)
        (default_dir / "config.yaml").write_text(
            "version: 1\nprofiles:\n  default:\n    applications: {}\n"
        )
        dotfiles_dir = default_dir / "dotfiles"
        dotfiles_dir.mkdir()
        (dotfiles_dir / ".zshrc").write_text("# zshrc content")
        (dotfiles_dir / ".gitconfig").write_text("[user]\n  name = Test")

    def test_moves_config_yaml_to_icloud(self, tmp_path):
        """init_icloud() moves config.yaml to iCloud dir when local config exists."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()
        default_dir = tmp_path / "default_config"
        self._setup_local_config(default_dir)

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_icloud()

        icloud_macsetup = icloud_drive / "macsetup"
        assert (icloud_macsetup / "config.yaml").exists()
        assert result["success"] is True
        assert result["migrated"] is True

    def test_moves_dotfiles_to_icloud(self, tmp_path):
        """init_icloud() moves dotfiles/ directory tree to iCloud dir."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()
        default_dir = tmp_path / "default_config"
        self._setup_local_config(default_dir)

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_icloud()

        icloud_macsetup = icloud_drive / "macsetup"
        assert (icloud_macsetup / "dotfiles" / ".zshrc").exists()
        assert (icloud_macsetup / "dotfiles" / ".gitconfig").exists()

    def test_deletes_local_files_after_copy(self, tmp_path):
        """init_icloud() deletes local config.yaml and dotfiles/ after moving to iCloud."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()
        default_dir = tmp_path / "default_config"
        self._setup_local_config(default_dir)

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_icloud()

        assert not (default_dir / "config.yaml").exists()
        assert not (default_dir / "dotfiles").exists()

    def test_preserves_file_contents(self, tmp_path):
        """init_icloud() preserves file contents during migration."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()
        default_dir = tmp_path / "default_config"
        self._setup_local_config(default_dir)
        original_content = (default_dir / "config.yaml").read_text()

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_icloud()

        icloud_macsetup = icloud_drive / "macsetup"
        assert (icloud_macsetup / "config.yaml").read_text() == original_content

    def test_pointer_file_written_after_move(self, tmp_path):
        """init_icloud() writes pointer file after migration."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()
        default_dir = tmp_path / "default_config"
        self._setup_local_config(default_dir)

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_icloud()

        pointer_path = default_dir / "config-dir"
        assert pointer_path.exists()
        assert pointer_path.read_text().strip() == str(icloud_drive / "macsetup")


class TestInitServiceConflict:
    """Tests for conflict detection (US2 - T019)."""

    def test_errors_when_both_configs_exist_no_force(self, tmp_path):
        """init_icloud() errors when both local and iCloud config.yaml exist without --force."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_macsetup = icloud_drive / "macsetup"
        icloud_macsetup.mkdir(parents=True)
        (icloud_macsetup / "config.yaml").write_text("icloud config")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_icloud(force=False)

        assert result["success"] is False
        assert result["error"] == "conflict"

    def test_force_overwrites_icloud_with_local(self, tmp_path):
        """init_icloud(force=True) overwrites iCloud config with local."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_macsetup = icloud_drive / "macsetup"
        icloud_macsetup.mkdir(parents=True)
        (icloud_macsetup / "config.yaml").write_text("old icloud config")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_icloud(force=True)

        assert result["success"] is True
        assert (icloud_macsetup / "config.yaml").read_text() == "local config"

    def test_conflict_error_includes_both_paths(self, tmp_path):
        """Conflict error includes both local and iCloud config paths."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_macsetup = icloud_drive / "macsetup"
        icloud_macsetup.mkdir(parents=True)
        (icloud_macsetup / "config.yaml").write_text("icloud config")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_icloud(force=False)

        assert "local_path" in result
        assert "icloud_path" in result


class TestInitServiceWriteFailure:
    """Tests for write failure handling (US2 - T019a)."""

    def test_reports_error_on_copy_oserror(self, tmp_path):
        """init_icloud() reports error when shutil.copy raises OSError."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        with patch("shutil.copy2", side_effect=OSError("Disk full")):
            result = service.init_icloud()

        assert result["success"] is False

    def test_error_includes_failed_path(self, tmp_path):
        """Error message includes the specific path that failed."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        with patch("shutil.copy2", side_effect=OSError("Disk full")):
            result = service.init_icloud()

        assert "path" in result or "message" in result

    def test_error_suggests_icloud_full(self, tmp_path):
        """Error message suggests iCloud Drive may be full or read-only."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        with patch("shutil.copy2", side_effect=OSError("Disk full")):
            result = service.init_icloud()

        message = result.get("message", "")
        assert "full" in message.lower() or "read-only" in message.lower()


class TestInitServiceExistingICloudConfig:
    """Tests for InitService.init_icloud() existing iCloud config case (US3 - T023)."""

    def test_detects_existing_config_in_icloud(self, tmp_path):
        """init_icloud() detects existing config.yaml in iCloud dir."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_macsetup = icloud_drive / "macsetup"
        icloud_macsetup.mkdir(parents=True)
        (icloud_macsetup / "config.yaml").write_text(
            "version: 1\nprofiles:\n  default:\n    applications: {}\n"
        )

        # No local config
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_icloud()

        assert result["success"] is True
        assert result["storage"] == "icloud"
        assert result.get("existing_config") is True

    def test_writes_pointer_without_copying(self, tmp_path):
        """init_icloud() writes pointer file without moving/copying anything."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_macsetup = icloud_drive / "macsetup"
        icloud_macsetup.mkdir(parents=True)
        (icloud_macsetup / "config.yaml").write_text("version: 1\n")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_icloud()

        # Pointer should be written
        pointer = default_dir / "config-dir"
        assert pointer.exists()
        assert pointer.read_text().strip() == str(icloud_macsetup)

        # Nothing should have been migrated
        assert result["migrated"] is False
        assert result["files_moved"] == 0


class TestInitServiceInitLocal:
    """Tests for InitService.init_local() (US4 - T027)."""

    def test_copies_config_from_icloud_to_local(self, tmp_path):
        """init_local() copies config.yaml from iCloud to default local dir."""
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        (icloud_dir / "config.yaml").write_text("icloud config content")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text(str(icloud_dir))

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_local()

        assert result["success"] is True
        assert (default_dir / "config.yaml").read_text() == "icloud config content"

    def test_copies_dotfiles_from_icloud_to_local(self, tmp_path):
        """init_local() copies dotfiles/ from iCloud to default local dir."""
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        dotfiles = icloud_dir / "dotfiles"
        dotfiles.mkdir()
        (dotfiles / ".zshrc").write_text("# zshrc")
        (dotfiles / ".gitconfig").write_text("[user]")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text(str(icloud_dir))

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_local()

        assert (default_dir / "dotfiles" / ".zshrc").read_text() == "# zshrc"
        assert (default_dir / "dotfiles" / ".gitconfig").read_text() == "[user]"

    def test_deletes_pointer_file(self, tmp_path):
        """init_local() deletes the pointer file."""
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text(str(icloud_dir))

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_local()

        assert not pointer.exists()

    def test_does_not_delete_icloud_copy(self, tmp_path):
        """init_local() does NOT delete the iCloud copy."""
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        (icloud_dir / "config.yaml").write_text("icloud config")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text(str(icloud_dir))

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_local()

        assert (icloud_dir / "config.yaml").exists()

    def test_errors_when_no_pointer_file(self, tmp_path):
        """init_local() errors when not currently using iCloud (no pointer file)."""
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_local()

        assert result["success"] is False


class TestInitLocalPreflightCheck:
    """Tests for init_local() pre-flight check on iCloud directory (Primary review finding)."""

    def test_errors_when_icloud_dir_not_accessible(self, tmp_path):
        """init_local() returns error when iCloud directory from pointer file is not accessible."""
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text("/nonexistent/icloud/path")

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_local()

        assert result["success"] is False
        assert result["error"] == "icloud_not_accessible"

    def test_does_not_delete_pointer_when_icloud_unreachable(self, tmp_path):
        """init_local() does NOT delete the pointer file when iCloud dir is unreachable."""
        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text("/nonexistent/icloud/path")

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_local()

        assert pointer.exists(), "Pointer file should NOT be deleted when iCloud is unreachable"


class TestInitLocalErrorHandling:
    """Tests for init_local() error handling for shutil operations (Review item 1)."""

    def test_handles_copy_oserror(self, tmp_path):
        """init_local() returns structured error when copy fails."""
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        (icloud_dir / "config.yaml").write_text("icloud config")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text(str(icloud_dir))

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        with patch("shutil.copy2", side_effect=OSError("Disk full")):
            result = service.init_local()

        assert result["success"] is False
        assert "error" in result

    def test_preserves_pointer_on_copy_failure(self, tmp_path):
        """init_local() does NOT delete pointer file when copy fails."""
        icloud_dir = tmp_path / "icloud_macsetup"
        icloud_dir.mkdir()
        (icloud_dir / "config.yaml").write_text("icloud config")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        pointer = default_dir / "config-dir"
        pointer.write_text(str(icloud_dir))

        mock_adapter = MagicMock()
        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        with patch("shutil.copy2", side_effect=OSError("Disk full")):
            service.init_local()

        assert pointer.exists(), "Pointer should not be deleted on copy failure"


class TestInitICloudExpandedErrorHandling:
    """Tests for init_icloud() expanded try/except scope (Review item 4)."""

    def test_handles_mkdir_failure(self, tmp_path):
        """init_icloud() returns error when mkdir fails."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            result = service.init_icloud()

        assert result["success"] is False

    def test_handles_pointer_write_failure_after_migration(self, tmp_path):
        """init_icloud() returns error when pointer write fails after migration."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        with patch(
            "macsetup.services.init.write_pointer_file", side_effect=OSError("Write failed")
        ):
            result = service.init_icloud()

        assert result["success"] is False


class TestMigrationHasLocalDotfilesCheck:
    """Tests for has_local checking dotfiles/ in addition to config.yaml (Review item 11)."""

    def test_detects_dotfiles_only_as_local_config(self, tmp_path):
        """init_icloud() detects local config when only dotfiles/ exists (no config.yaml)."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        dotfiles_dir = default_dir / "dotfiles"
        dotfiles_dir.mkdir()
        (dotfiles_dir / ".zshrc").write_text("# zshrc")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        result = service.init_icloud()

        # Should have migrated the dotfiles
        assert result["success"] is True
        assert result["migrated"] is True
        icloud_macsetup = icloud_drive / "macsetup"
        assert (icloud_macsetup / "dotfiles" / ".zshrc").exists()


class TestMigrationDeleteFailureSeparation:
    """Tests for separating copy vs delete failures in migration (Review item 12)."""

    def test_delete_failure_after_successful_copy_not_write_failure(self, tmp_path):
        """When copy succeeds but delete fails, error should not say 'write_failure'."""
        icloud_drive = tmp_path / "icloud_drive"
        icloud_drive.mkdir()

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()
        (default_dir / "config.yaml").write_text("local config")

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)

        original_unlink = Path.unlink

        def fail_unlink(self, *args, **kwargs):
            if "config.yaml" in str(self):
                raise OSError("Permission denied")
            return original_unlink(self, *args, **kwargs)

        with patch.object(Path, "unlink", fail_unlink):
            result = service.init_icloud()

        # Data should be safe in iCloud, error should indicate cleanup failure not write failure
        assert result["success"] is False
        assert result.get("error") != "write_failure"


class TestInitServiceEndToEnd:
    """Tests for end-to-end flow (US3 - T024)."""

    def test_init_icloud_then_get_config_dir_resolves(self, tmp_path):
        """init_icloud with existing iCloud config then get_config_dir resolves to iCloud path."""
        from macsetup.cli import get_config_dir

        icloud_drive = tmp_path / "icloud_drive"
        icloud_macsetup = icloud_drive / "macsetup"
        icloud_macsetup.mkdir(parents=True)
        (icloud_macsetup / "config.yaml").write_text("version: 1\n")

        default_dir = tmp_path / "default_config"
        default_dir.mkdir()

        mock_adapter = MagicMock()
        mock_adapter.is_icloud_available.return_value = True
        mock_adapter.get_icloud_drive_path.return_value = icloud_drive

        service = InitService(icloud_adapter=mock_adapter, default_config_dir=default_dir)
        service.init_icloud()

        # Now get_config_dir should resolve to iCloud path
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("macsetup.cli.DEFAULT_CONFIG_DIR", default_dir),
        ):
            resolved = get_config_dir()
            assert resolved == icloud_macsetup
