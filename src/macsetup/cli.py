"""CLI entry point for macsetup."""

import argparse
import os
import sys
from pathlib import Path

from macsetup import __version__

# Default config directory
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "macsetup"


def get_config_dir() -> Path:
    """Get the configuration directory, respecting environment variable override."""
    env_dir = os.environ.get("MACSETUP_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)
    return DEFAULT_CONFIG_DIR


def add_global_options(parser: argparse.ArgumentParser) -> None:
    """Add global options that apply to all commands."""
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=None,
        metavar="PATH",
        help=f"Override config directory (default: {DEFAULT_CONFIG_DIR})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format (for scripting)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug output",
    )


def cmd_capture(args: argparse.Namespace) -> int:
    """Handle the capture command."""
    print("capture command not yet implemented")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    """Handle the setup command."""
    import json

    from macsetup.models.config import load_config
    from macsetup.services.setup import SetupService

    config_path = args.resolved_config_dir / "config.yaml"

    # Check if config exists
    if not config_path.exists():
        if args.json:
            print(json.dumps({"success": False, "error": "Configuration file not found"}))
        else:
            print(f"Error: Configuration file not found: {config_path}")
            print("Run 'macsetup capture' first to create a configuration.")
        return 2

    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": f"Invalid configuration: {e}"}))
        else:
            print(f"Error: Invalid configuration file: {e}")
        return 2

    # Check if profile exists
    if args.profile not in config.profiles:
        if args.json:
            print(json.dumps({"success": False, "error": f"Profile not found: {args.profile}"}))
        else:
            print(f"Error: Profile '{args.profile}' not found")
            print(f"Available profiles: {', '.join(config.profiles.keys())}")
        return 2

    # Dry-run mode
    if args.dry_run:
        if not args.quiet:
            print(f"Dry-run: would apply profile '{args.profile}'")
        # TODO: implement preview output
        return 0

    # Progress callback
    def progress(message: str, current: int, total: int):
        if not args.quiet and not args.json:
            print(f"  [{current}/{total}] {message}")

    # Create and run setup service
    service = SetupService(
        config=config,
        config_dir=args.resolved_config_dir,
        profile=args.profile,
        force=args.force,
        skip_dotfiles=args.no_dotfiles,
        skip_preferences=args.no_preferences,
        progress_callback=progress,
    )

    if not args.quiet and not args.json:
        print(f"Applying configuration from {config_path} (profile: {args.profile})")
        print()

    result = service.run(resume=args.resume)

    # Output results
    if args.json:
        output = {
            "success": result.success and result.failed_count == 0,
            "completed": result.completed_count,
            "failed": result.failed_count,
            "failures": [
                {"type": f.type, "identifier": f.identifier, "error": f.error}
                for f in result.failed_items
            ],
            "manual_required": [
                {"name": m.name, "url": m.url} for m in result.manual_apps
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        if not args.quiet:
            print()
            if result.failed_count > 0:
                print(f"Setup complete with {result.failed_count} failure(s):")
                for f in result.failed_items:
                    print(f"  - {f.type}:{f.identifier}: {f.error}")
            else:
                print("Setup complete!")

            if result.manual_apps:
                print()
                print("Manual steps required:")
                for m in result.manual_apps:
                    if m.url:
                        print(f"  - {m.name}: {m.url}")
                    else:
                        print(f"  - {m.name}")

    # Return appropriate exit code
    if result.interrupted:
        return 130
    if result.failed_count > 0:
        return 3
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    """Handle the preview command."""
    print("preview command not yet implemented")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Handle the sync command."""
    print("sync command not yet implemented")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    """Handle the profile command."""
    print("profile command not yet implemented")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle the validate command."""
    print("validate command not yet implemented")
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="macsetup",
        description="macOS Configuration Sync CLI - Capture, store, and restore macOS machine configurations",
    )
    add_global_options(parser)

    subparsers = parser.add_subparsers(dest="command", title="commands")

    # capture command
    capture_parser = subparsers.add_parser(
        "capture",
        help="Capture current machine configuration",
        description="Capture current machine configuration to a YAML file.",
    )
    capture_parser.add_argument(
        "--profile",
        default="default",
        metavar="NAME",
        help="Profile to capture to (default: default)",
    )
    capture_parser.add_argument(
        "--dotfiles",
        metavar="PATHS",
        help="Additional dotfiles to capture (comma-separated)",
    )
    capture_parser.add_argument(
        "--preferences",
        metavar="DOMAINS",
        help="Additional preference domains (comma-separated)",
    )
    capture_parser.add_argument(
        "--skip-apps",
        action="store_true",
        help="Skip application capture",
    )
    capture_parser.add_argument(
        "--skip-dotfiles",
        action="store_true",
        help="Skip dotfile capture",
    )
    capture_parser.add_argument(
        "--skip-preferences",
        action="store_true",
        help="Skip preference capture",
    )
    capture_parser.set_defaults(func=cmd_capture)

    # setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Apply configuration to current machine",
        description="Apply configuration from YAML file to current machine.",
    )
    setup_parser.add_argument(
        "--profile",
        default="default",
        metavar="NAME",
        help="Profile to apply (default: default)",
    )
    setup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    setup_parser.add_argument(
        "--include",
        metavar="ITEMS",
        help="Only install these items (comma-separated)",
    )
    setup_parser.add_argument(
        "--exclude",
        metavar="ITEMS",
        help="Skip these items (comma-separated)",
    )
    setup_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume interrupted setup",
    )
    setup_parser.add_argument(
        "--force",
        action="store_true",
        help="Reinstall already-installed items",
    )
    setup_parser.add_argument(
        "--no-dotfiles",
        action="store_true",
        help="Skip dotfile setup",
    )
    setup_parser.add_argument(
        "--no-preferences",
        action="store_true",
        help="Skip preference setup",
    )
    setup_parser.set_defaults(func=cmd_setup)

    # preview command
    preview_parser = subparsers.add_parser(
        "preview",
        help="Show what setup would do",
        description="Preview what setup would do without making changes.",
    )
    preview_parser.add_argument(
        "--profile",
        default="default",
        metavar="NAME",
        help="Profile to preview (default: default)",
    )
    preview_parser.add_argument(
        "--diff",
        action="store_true",
        help="Show what's different from current state",
    )
    preview_parser.set_defaults(func=cmd_preview)

    # sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Manage background sync daemon",
        description="Manage background sync daemon.",
    )
    sync_subparsers = sync_parser.add_subparsers(dest="sync_command", title="subcommands")

    sync_start = sync_subparsers.add_parser("start", help="Start background sync")
    sync_start.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="MINUTES",
        help="Sync interval in minutes (default: 60)",
    )
    sync_start.add_argument(
        "--watch",
        action="store_true",
        default=True,
        help="Watch dotfiles for changes (default: true)",
    )

    sync_subparsers.add_parser("stop", help="Stop background sync")
    sync_subparsers.add_parser("status", help="Show sync status")
    sync_subparsers.add_parser("now", help="Run sync immediately")
    sync_parser.set_defaults(func=cmd_sync)

    # profile command
    profile_parser = subparsers.add_parser(
        "profile",
        help="Manage configuration profiles",
        description="Manage configuration profiles.",
    )
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_command", title="subcommands"
    )

    profile_subparsers.add_parser("list", help="List all profiles")

    profile_show = profile_subparsers.add_parser("show", help="Show profile details")
    profile_show.add_argument("name", help="Profile name")

    profile_create = profile_subparsers.add_parser("create", help="Create new profile")
    profile_create.add_argument("name", help="Profile name")

    profile_delete = profile_subparsers.add_parser("delete", help="Delete profile")
    profile_delete.add_argument("name", help="Profile name")

    profile_diff = profile_subparsers.add_parser("diff", help="Compare two profiles")
    profile_diff.add_argument("name1", help="First profile name")
    profile_diff.add_argument("name2", help="Second profile name")

    profile_parser.set_defaults(func=cmd_profile)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate configuration file",
        description="Validate configuration file against schema.",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings",
    )
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for macsetup CLI."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    # If no command specified, show help
    if parsed.command is None:
        parser.print_help()
        return 0

    # Resolve config directory
    config_dir = parsed.config_dir or get_config_dir()

    # Store resolved config dir in namespace for commands to use
    parsed.resolved_config_dir = config_dir

    # Call the command handler
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
